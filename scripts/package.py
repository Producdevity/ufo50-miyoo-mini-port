#!/usr/bin/env python3
"""Package the Mini install and exact source separately; keep device builds private."""
import argparse
import json
import re
import shutil
import subprocess
import tarfile
import tempfile
import zipfile
from pathlib import Path
from artifact import ROOT, inspect_arm32, sha256, source_state


def check_performance_build(record):
    expected = {'ENABLE_VM_TRACING', 'ENABLE_VM_GML_PROFILER', 'ENABLE_VM_OPCODE_PROFILER'}
    features = record.get('diagnostic_features', {})
    if set(features) != expected or any(value != 'OFF' for value in features.values()):
        raise ValueError('Disable VM tracing and profiling before packaging')
    if record.get('interprocedural_optimization') is not True:
        raise ValueError('Enable interprocedural optimization before packaging')


def build_record(target, source):
    binary = ROOT / 'artifacts' / target / 'butterscotch'
    record = json.loads((binary.parent / 'build.json').read_text())
    if record['target'] != target or record['source'] != source:
        raise ValueError('Rebuild from this clean source commit before packaging')
    if record['runtime_sha256'] != sha256(binary):
        raise ValueError('Binary differs from its recorded successful build')
    if record['elf'] != inspect_arm32(binary):
        raise ValueError('ELF ABI differs from the build record')
    check_performance_build(record)
    return binary, record


def release_version(value):
    if not re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', value):
        raise ValueError('Expected a version such as 0.1.0')
    return value


def package(target, source, output, version=None):
    if version is not None:
        release_version(version)
        if target != 'armhf':
            raise ValueError('Versioned releases contain only the Miyoo Mini install')
    binary, record = build_record(target, source)
    with tempfile.TemporaryDirectory(prefix='ufo50-package-') as directory:
        stage = Path(directory)
        if target == 'armhf':
            game = stage / 'Roms/PORTS/Games/UFO50'
            game.mkdir(parents=True)
            shutil.copy2(ROOT / 'port/script.sh', game / 'script.sh')
            shortcut = stage / 'Roms/PORTS/Shortcuts/Action/UFO50.notfound'
            shortcut.parent.mkdir(parents=True)
            shutil.copy2(ROOT / 'port/UFO50.notfound', shortcut)
            artwork = stage / 'Roms/PORTS/Imgs/UFO50.png'
            artwork.parent.mkdir(parents=True)
            shutil.copy2(ROOT / 'port/artwork/UFO50.png', artwork)
            name = f'ufo50-miyoo-mini-v{version}.zip' if version else 'ufo50-miyoo-mini-development.zip'
        else:
            game = stage / 'mmc/.ufo50-dev'
            game.mkdir(parents=True)
            shutil.copy2(ROOT / 'port/muos/launch.sh', game / 'launch.sh')
            shortcut = stage / 'sdcard/ROMS/Ports/UFO50.sh'
            shortcut.parent.mkdir(parents=True)
            shutil.copy2(ROOT / 'port/muos/UFO50.sh', shortcut)
            name = 'ufo50-muos-sp-development.zip'
        (game / 'bin').mkdir()
        shutil.copy2(binary, game / 'bin/butterscotch')
        (game / 'bin/butterscotch').chmod(0o755)
        (game / 'gamefiles').mkdir()
        if not version:
            (game / '_required_files.txt').write_text(
                'Supply your owned Windows UFO 50 assets in gamefiles/.\n'
                'Copy the Windows game folder contents here; data.win must be in gamefiles/.\n'
                'See README.txt for installation instructions.\n')
        for document in ['LICENSE', 'NOTICE']:
            shutil.copy2(ROOT / document, game / document)
        if version:
            shutil.copy2(ROOT / 'port/README.txt', game / 'README.txt')
            shutil.copy2(ROOT / 'licenses/THIRD_PARTY.txt', game / 'THIRD_PARTY.txt')
        else:
            shutil.copy2(ROOT / 'README.md', game / 'README.md')
            shutil.copy2(ROOT / 'port/README.txt', game / 'README.txt')
        source_archive = stage / 'source.tar.gz'
        subprocess.run(['git', 'archive', '--format=tar.gz', '--output=' + str(source_archive),
                        source['commit']], cwd=ROOT, check=True)
        with tarfile.open(source_archive) as source_tar:
            for entry in source_tar.getmembers():
                parts = Path(entry.name).parts
                if any(part in ('.local', 'artifacts', 'gamefiles', 'saves') for part in parts):
                    raise ValueError(f'Private directory in source archive: {entry.name}')
                if entry.name.endswith(('.win', '.yytex', '.ufo', '.exe')):
                    raise ValueError(f'Game data in source archive: {entry.name}')
        manifest = dict(record, status='release' if version else 'development', gamefiles_included=False,
                        source_archive_sha256=sha256(source_archive),
                        physical_miyoo_validation=False)
        if version:
            source_name = f'ufo50-miyoo-mini-v{version}-source.tar.gz'
            shutil.copy2(source_archive, output / source_name)
            shutil.copy2(ROOT / 'port/artwork/UFO50.png', output / 'UFO50.png')
            manifest.update(version=version, source_archive=source_name,
                source_url=f'https://github.com/Producdevity/ufo50-miyoo-mini-port/releases/download/v{version}/{source_name}')
            (game / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        else:
            (stage / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        archive = output / name
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as package_zip:
            for file in sorted(stage.rglob('*')):
                if version and file == source_archive:
                    continue
                if file.is_file() or file == game / 'gamefiles':
                    package_zip.write(file, file.relative_to(stage))
        with zipfile.ZipFile(archive) as package_zip:
            if package_zip.testzip() is not None:
                raise ValueError('Package failed CRC verification')
            if any(Path(name).suffix in ('.win', '.yytex', '.ufo', '.exe')
                   for name in package_zip.namelist()):
                raise ValueError('Game data found in package')
        return archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', choices=['armhf', 'sp', 'all'], default='armhf')
    parser.add_argument('--version', help='Mini release version; defaults to VERSION for the Mini target')
    args = parser.parse_args()
    source = source_state()
    if source['dirty']:
        parser.error('Commit verified source changes, then rebuild from a clean tree')
    version = args.version
    if version is None and args.target == 'armhf':
        version = (ROOT / 'VERSION').read_text().strip()
    try:
        if version:
            release_version(version)
            if args.target != 'armhf':
                raise ValueError('Versioned releases contain only the Miyoo Mini install')
    except ValueError as error:
        parser.error(str(error))
    output = ROOT / 'artifacts/release'
    if version:
        output /= 'v' + version
    output.mkdir(parents=True, exist_ok=True)
    targets = ['armhf', 'sp'] if args.target == 'all' else [args.target]
    try:
        archives = [package(target, source, output, version) for target in targets]
        if version:
            archives.extend([output / f'ufo50-miyoo-mini-v{version}-source.tar.gz',
                             output / 'UFO50.png'])
    except (ValueError, FileNotFoundError) as error:
        parser.error(str(error))
    (output / 'SHA256SUMS').write_text(''.join(f'{sha256(archive)}  {archive.name}\n'
                                            for archive in archives))
    for archive in archives:
        print(archive)


if __name__ == '__main__':
    main()
