#!/usr/bin/env python3
"""Non-destructive UFO 50 asset import and structural audit. Standard library only."""
import argparse
import hashlib
import json
import mmap
from pathlib import Path, PurePosixPath
import shutil
import stat
import struct
import tempfile
import zipfile

MAX_TOTAL = 2 * 1024**3


def u32(data, offset):
    if offset < 0 or offset + 4 > len(data):
        raise ValueError(f'Invalid u32 offset {offset}')
    return struct.unpack_from('<I', data, offset)[0]


def chunks(data):
    if len(data) < 8 or data[:4] != b'FORM' or u32(data, 4) + 8 != len(data):
        raise ValueError('Invalid FORM header or length')
    result = {}
    offset = 8
    while offset < len(data):
        if offset + 8 > len(data):
            raise ValueError('Truncated chunk header')
        name = data[offset:offset+4].decode('ascii')
        length = u32(data, offset+4)
        if name in result or offset + 8 + length > len(data):
            raise ValueError(f'Duplicate or truncated {name} chunk')
        result[name] = (offset+8, length)
        offset += 8 + length
    for name in ('GEN8', 'CODE', 'STRG'):
        if name not in result:
            raise ValueError(f'Missing {name}; a VM game is required')
    return result


def string(data, pointer):
    if pointer == 0:
        return ''
    length = u32(data, pointer-4)
    if length > 1024**2 or pointer + length >= len(data) or data[pointer+length] != 0:
        raise ValueError('Invalid string pointer')
    return data[pointer:pointer+length].decode('utf-8')


def table(data, offset, end=None):
    count = u32(data, offset)
    end = len(data) if end is None else end
    if offset + 4 + count * 4 > end:
        raise ValueError('Invalid pointer/list count')
    return [u32(data, offset+4+i*4) for i in range(count)]


def safe_relative(name):
    path = PurePosixPath(name)
    if not name or '\\' in name or path.is_absolute() or '..' in path.parts or any(':' in p for p in path.parts):
        raise ValueError(f'Unsafe asset path: {name}')
    return path


def selected(path):
    if path.name.startswith('._') or '__MACOSX' in path.parts:
        return False
    if len(path.parts) == 1:
        return path.name in ('data.win', 'options.ini') or (path.name.startswith('audiogroup') and path.suffix == '.dat')
    return (path.parts[0] == 'textures' and path.suffix == '.yytex') or (path.parts[0] == 'fonts' and path.suffix == '.ttf') or (path.parts[0] == 'ext' and path.suffix == '.json')


def import_zip(source, destination):
    """Import to a new directory only. Original archive, executables and saves untouched."""
    source, destination = Path(source).resolve(), Path(destination).absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError(f'Destination already exists: {destination}')
    with zipfile.ZipFile(source) as archive:
        candidates = []
        for member in archive.infolist():
            path = safe_relative(member.filename)
            if stat.S_ISLNK(member.external_attr >> 16):
                raise ValueError('Archive contains a symbolic link')
            if path.name == 'data.win' and '__MACOSX' not in path.parts:
                candidates.append(path)
        if len(candidates) != 1:
            raise ValueError('Archive must contain exactly one data.win')
        prefix = candidates[0].parent
        files, seen, total = [], set(), 0
        for member in archive.infolist():
            path = safe_relative(member.filename)
            if member.is_dir() or not path.is_relative_to(prefix):
                continue
            relative = path.relative_to(prefix)
            if not selected(relative):
                continue
            key = str(relative).casefold()
            if key in seen:
                raise ValueError(f'Duplicate asset: {relative}')
            seen.add(key)
            total += member.file_size
            if total > MAX_TOTAL:
                raise ValueError('Selected assets exceed the 2 GiB import limit')
            files.append((member, relative))
        destination.parent.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix='.ufo50-import-', dir=destination.parent))
        try:
            for member, relative in files:
                out = stage.joinpath(*relative.parts)
                out.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as src, out.open('xb') as dst:
                    shutil.copyfileobj(src, dst)
            audit(stage)  # reject malformed data or missing external textures before promotion
            stage.rename(destination)
        except BaseException:
            shutil.rmtree(stage)
            raise
    return {'destination': str(destination), 'selected_files': len(files), 'bytes': total, 'archive_sha256': sha256(source)}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024**2), b''):
            digest.update(block)
    return digest.hexdigest()


def audit(directory):
    root = Path(directory).resolve()
    path = root/'data.win'
    with path.open('rb') as file, mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as data:
        cs = chunks(data)
        gen = cs['GEN8'][0]
        if data[gen+1] != 17:
            raise ValueError('This prototype targets bytecode 17 only')
        if cs['GEN8'][1] < 72:
            raise ValueError('Truncated GEN8')
        report = {
            'data_sha256': sha256(path), 'data_bytes': len(data),
            'name': string(data, u32(data, gen+4)), 'bytecode_version': data[gen+1],
            'gen8_version_fields_not_reliable_engine_version': list(struct.unpack_from('<4I', data, gen+44)),
            'native_size': list(struct.unpack_from('<2I', data, gen+60)),
            'chunks': {k: {'offset': v[0]-8, 'bytes': v[1]} for k,v in cs.items()},
            'counts': {k: u32(data, cs[k][0]) for k in ('ROOM','SPRT','OBJT','TXTR','CODE','FUNC','AGRP') if k in cs},
            'texture_groups': [],
        }
        if 'FUNC' in cs:
            base, size = cs['FUNC']; count = u32(data, base)
            if 4 + count*12 > size: raise ValueError('Unsupported FUNC layout')
            report['referenced_functions'] = [string(data, u32(data,base+4+i*12)) for i in range(count)]
        if 'TGIN' in cs and 'TXTR' in cs:
            base,size = cs['TGIN']
            if u32(data,base) != 1: raise ValueError('Unsupported TGIN layout')
            txbase,txsize = cs['TXTR']; textures = table(data,txbase,txbase+txsize)
            for pointer in table(data,base+4,base+size):
                if not base <= pointer <= base+size-20: raise ValueError('Invalid TGIN group pointer')
                name,directory,extension = [string(data,u32(data,pointer+i*4)) for i in range(3)]
                load_type=u32(data,pointer+12)
                pages=table(data,u32(data,pointer+16),base+size)
                group={'name':name,'load_type':load_type,'pages':[],'rgba_bytes':0}
                for page in pages:
                    if page >= len(textures): raise ValueError('Invalid texture page index')
                    entry=textures[page]
                    if not txbase <= entry <= txbase+txsize-28: raise ValueError('Unsupported TXTR entry')
                    width,height,index,blob=struct.unpack_from('<4I',data,entry+12)
                    item={'id':page,'width':width,'height':height,'index_in_group':index}
                    if load_type == 2:
                        relative=safe_relative(f'{directory}/{name}_{index}{extension}')
                        external=root.joinpath(*relative.parts)
                        if not external.resolve().is_relative_to(root): raise ValueError('External texture leaves data directory')
                        with external.open('rb') as f: header=f.read(12)
                        if len(header)<12 or header[:4]!=b'2zoq': raise ValueError('Expected modern QOI+BZip2 texture')
                        w,h=struct.unpack_from('<HH',header,4)
                        if (w,h)!=(width,height): raise ValueError('Texture dimensions disagree')
                        item.update(file=str(relative),bytes=external.stat().st_size,format='2zoq')
                    group['rgba_bytes']+=width*height*4
                    group['pages'].append(item)
                report['texture_groups'].append(group)
        report['all_texture_rgba_bytes'] = sum(g['rgba_bytes'] for g in report['texture_groups'])
        report['startup_texture_rgba_bytes'] = sum(g['rgba_bytes'] for g in report['texture_groups'] if g['name'] in ('texturegroup00_intro','texturegroup00_library','texturegroup00_shared'))
        report['audio_groups_on_disk']=[{'name':p.name,'bytes':p.stat().st_size} for p in sorted(root.glob('audiogroup*.dat'))]
        report['interpretation']='Static asset sizes, not measured runtime RSS or a compatibility pass.'
        return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    imp=sub.add_parser('import');imp.add_argument('archive',type=Path);imp.add_argument('destination',type=Path)
    au=sub.add_parser('audit');au.add_argument('directory',type=Path);au.add_argument('--output',type=Path)
    args=parser.parse_args()
    try:
        result=import_zip(args.archive,args.destination) if args.action=='import' else audit(args.directory)
        text=json.dumps(result,indent=2)+'\n'
        if getattr(args,'output',None):
            args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(text)
            print(f'Wrote {args.output}')
        else:print(text,end='')
    except (ValueError,OSError,zipfile.BadZipFile,UnicodeError,struct.error) as e:
        parser.exit(1,f'Error: {e}\n')

if __name__=='__main__':main()
