"""Source and ARM32 artifact checks shared by builds and packaging."""
import hashlib
import re
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def source_state():
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT))
    return {'commit': commit, 'dirty': dirty}


def inspect_arm32(path):
    data = Path(path).read_bytes()
    if len(data) < 52 or data[:6] != b'\x7fELF\x01\x01':
        raise ValueError('Expected a little-endian ELF32 executable')
    header = struct.unpack_from('<HHIIIIIHHHHHH', data, 16)
    kind, machine, _, _, phoff, shoff, flags, _, phsize, phnum, shsize, shnum, _ = header
    if machine != 40 or kind not in (2, 3):
        raise ValueError('Expected an ARM executable, not a library or another architecture')
    if (flags >> 24) != 5 or not (flags & 0x400):
        raise ValueError('Expected ARM EABI5 hard-float ABI')
    if phsize != 32 or shsize != 40 or not shnum:
        raise ValueError('Unexpected or missing ELF tables')
    if phoff + phnum * phsize > len(data) or shoff + shnum * shsize > len(data):
        raise ValueError('Truncated ELF tables')

    interpreter = None
    for i in range(phnum):
        segment = struct.unpack_from('<IIIIIIII', data, phoff + i * phsize)
        if segment[0] == 3:
            interpreter = data[segment[1]:segment[1] + segment[4]].rstrip(b'\0').decode()
    if interpreter != '/lib/ld-linux-armhf.so.3':
        raise ValueError(f'Unexpected dynamic loader: {interpreter}')

    sections = [struct.unpack_from('<IIIIIIIIII', data, shoff + i * shsize) for i in range(shnum)]
    needed, versions = [], []
    for section in sections:
        _, section_type, _, _, offset, size, link, _, _, entry_size = section
        if offset + size > len(data) and section_type != 8:
            raise ValueError('Truncated ELF section')
        if section_type not in (6, 0x6ffffffe):
            continue
        if link >= len(sections):
            raise ValueError('Invalid ELF string-table link')
        strings = sections[link]
        string_data = data[strings[4]:strings[4] + strings[5]]

        def string(index):
            if not 0 <= index < len(string_data):
                raise ValueError('Invalid ELF string offset')
            return string_data[index:].split(b'\0', 1)[0].decode()

        if section_type == 6:
            if entry_size != 8 or size % 8:
                raise ValueError('Unexpected ELF dynamic table')
            for pos in range(offset, offset + size, 8):
                tag, value = struct.unpack_from('<iI', data, pos)
                if tag in (15, 29):
                    raise ValueError('Runtime search paths must not be embedded in packages')
                if tag == 1:
                    needed.append(string(value))
        else:
            pos, end = offset, offset + size
            seen = set()
            while pos < end:
                if pos in seen or pos + 16 > end:
                    raise ValueError('Invalid ELF version requirements')
                seen.add(pos)
                _, count, _, aux, next_record = struct.unpack_from('<HHIII', data, pos)
                auxiliary = pos + aux
                for _ in range(count):
                    if auxiliary + 16 > end:
                        raise ValueError('Truncated ELF version requirement')
                    _, _, _, name, next_aux = struct.unpack_from('<IHHII', data, auxiliary)
                    versions.append(string(name))
                    auxiliary += next_aux
                if not next_record:
                    break
                pos += next_record
    glibc = sorted({tuple(map(int, version.split('_', 1)[1].split('.')))
                    for version in versions if re.fullmatch(r'GLIBC_\d+(?:\.\d+)+', version)})
    if not glibc or glibc[-1] > (2, 28):
        raise ValueError(f'Expected glibc requirements no newer than 2.28: {glibc}')
    allowed = {'libSDL-1.2.so.0', 'libSDL-1.2.so.1', 'libc.so.6', 'libm.so.6',
               'libpthread.so.0', 'libdl.so.2', 'librt.so.1', 'libgcc_s.so.1'}
    if set(needed) - allowed or not any(name.startswith('libSDL-1.2.so.') for name in needed):
        raise ValueError(f'Unexpected runtime dependencies: {needed}')
    return {'architecture': 'ARM32 EABI5 hard-float', 'interpreter': interpreter,
            'needed': needed, 'max_glibc': '.'.join(map(str, glibc[-1]))}
