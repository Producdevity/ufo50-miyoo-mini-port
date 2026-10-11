#!/usr/bin/env python3
"""Stage and verify a built Mini package while preserving existing game files and saves."""
import argparse
import datetime
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from artifact import ROOT, inspect_arm32, sha256, source_state
from package import build_record

GAME = 'Roms/PORTS/Games/UFO50'
SHORTCUT = 'Roms/PORTS/Shortcuts/Action/UFO50'
SAVE = 'Saves/CurrentProfile/saves/UFO50'
METADATA = {'.DS_Store', 'Thumbs.db'}


def metadata(path):
    return path.name.startswith('._') or path.name in METADATA


def manifest(directory):
    if not directory.exists():
        return {}
    result = {}
    for file in sorted(directory.rglob('*')):
        if file.is_symlink():
            raise ValueError(f'Symlink in preserved files: {file}')
        if file.is_file() and not metadata(file):
            result[file.relative_to(directory).as_posix()] = sha256(file)
    return result


def unpack_package(archive, directory):
    source = source_state()
    if source['dirty']:
        raise ValueError('Deploy from a clean source checkout')
    _, expected_record = build_record('armhf', source)
    allowed = {'manifest.json', 'source.tar.gz', SHORTCUT + '.notfound'} | {
        GAME + '/' + name for name in ['bin/butterscotch', 'script.sh', 'README.md',
                                      'LICENSE', 'NOTICE', '_required_files.txt']}
    with zipfile.ZipFile(archive) as package:
        if package.testzip():
            raise ValueError('Package CRC verification failed')
        for entry in package.infolist():
            parts = PurePosixPath(entry.filename).parts
            if not parts or entry.filename.startswith('/') or '..' in parts or '\\' in entry.filename:
                raise ValueError('Unsafe package path')
            if (entry.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Package symlink refused')
            if entry.filename not in allowed and entry.filename != GAME + '/gamefiles/':
                raise ValueError('Unexpected package member')
            if entry.filename == GAME + '/gamefiles/' and not entry.is_dir():
                raise ValueError('Expected an empty gamefiles directory')
            if any(part in ('gamefiles', 'saves', '.local', 'artifacts') for part in parts) and not entry.is_dir():
                raise ValueError('Private files found in distributable package')
        package.extractall(directory)
    record = json.loads((directory / 'manifest.json').read_text())
    binary = directory / GAME / 'bin/butterscotch'
    if record['source'] != source or record['target'] != 'armhf' or record['gamefiles_included']:
        raise ValueError('Wrong source, target or game-data boundary')
    if record['runtime_sha256'] != expected_record['runtime_sha256']:
        raise ValueError('Package differs from the verified local build')
    if sha256(binary) != record['runtime_sha256'] or inspect_arm32(binary) != record['elf']:
        raise ValueError('Runtime verification failed')
    if sha256(directory / 'source.tar.gz') != record['source_archive_sha256']:
        raise ValueError('Source archive verification failed')
    for source_name, packaged_name in [('port/script.sh', GAME + '/script.sh'),
                                        ('port/UFO50.notfound', SHORTCUT + '.notfound'),
                                        ('README.md', GAME + '/README.md'),
                                        ('LICENSE', GAME + '/LICENSE'), ('NOTICE', GAME + '/NOTICE')]:
        if sha256(ROOT / source_name) != sha256(directory / packaged_name):
            raise ValueError('Packaged source file differs from the clean checkout')
    return record


def copy_assets(source, destination):
    for item in source.iterdir():
        if metadata(item):
            continue
        if item.is_symlink():
            raise ValueError('Game asset symlinks refused')
        target = destination / item.name
        if item.is_dir():
            shutil.copytree(item, target, ignore=lambda _, names: [name for name in names if name.startswith('._') or name in METADATA])
        else:
            shutil.copy2(item, target)


def deploy(sd, package, gamefiles, backup_root):
    """Caller validates the real mount; this function also supports an isolated fixture."""
    if not (sd / 'Emu/PORTS/launch_standalone.sh').is_file():
        raise ValueError('Onion Ports Collection launcher is missing')
    target = sd / GAME
    saves = sd / SAVE
    owned = target / 'gamefiles'
    if owned.exists() and any(owned.iterdir()):
        if gamefiles is not None:
            raise ValueError('Existing gamefiles are preserved; omit --gamefiles')
        gamefiles = owned
    if gamefiles is None or not (gamefiles / 'data.win').is_file():
        raise ValueError('Supply owned assets with --gamefiles for a first installation')
    asset_before = manifest(gamefiles)
    save_before = manifest(saves)
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + str(os.getpid())
    backup = backup_root / stamp
    backup.mkdir(parents=True, exist_ok=False)
    staged = target.parent / ('.UFO50.new.' + stamp)
    previous = target.parent / ('.UFO50.old.' + stamp)
    shortcuts = [sd / (SHORTCUT + extension) for extension in ('.port', '.notfound')]
    activated = False
    promoted_old = False
    try:
        with tempfile.TemporaryDirectory(prefix='ufo50-package-check-') as temporary:
            unpacked = Path(temporary)
            record = unpack_package(package, unpacked)
            with tarfile.open(backup / 'previous.tar.gz', 'w:gz') as archive:
                for relative in [GAME, SAVE, SHORTCUT + '.port', SHORTCUT + '.notfound']:
                    path = sd / relative
                    if path.exists():
                        archive.add(path, arcname=relative)
            (backup / 'before.json').write_text(json.dumps(dict(saves=save_before, gamefiles=asset_before), indent=2) + '\n')
            expected = manifest(unpacked / GAME)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(unpacked / GAME, staged)
            (staged / 'gamefiles').mkdir(exist_ok=True)
            copy_assets(gamefiles, staged / 'gamefiles')
            for file in staged.rglob('*'):
                if file.is_file() and metadata(file):
                    file.unlink()
            for relative, digest in expected.items():
                if sha256(staged / relative) != digest:
                    raise ValueError('Staged runtime file differs from the package')
            if manifest(staged / 'gamefiles') != asset_before:
                raise ValueError('Staged game files differ from the source')
            if target.exists():
                target.rename(previous)
                promoted_old = True
            staged.rename(target)
            activated = True
            shortcut = sd / (SHORTCUT + '.port')
            shortcut.parent.mkdir(parents=True, exist_ok=True)
            next_shortcut = shortcut.with_suffix('.next')
            shutil.copy2(unpacked / (SHORTCUT + '.notfound'), next_shortcut)
            next_shortcut.replace(shortcut)
            for old in shortcuts:
                if old.suffix == '.notfound' and old.exists():
                    old.unlink()
            # Match the mounted Onion importer's filename-only presence check.
            if not any(file.is_file() and file.name.lower() == 'data.win'
                       for file in target.glob('*/*')):
                raise ValueError('Onion game-data check failed')
            for relative, digest in expected.items():
                if sha256(target / relative) != digest:
                    raise ValueError('Installed runtime file differs from the package')
            if manifest(target / 'gamefiles') != asset_before or manifest(saves) != save_before:
                raise ValueError('Installed assets or preserved saves differ')
            if sha256(shortcut) != sha256(unpacked / (SHORTCUT + '.notfound')):
                raise ValueError('Installed shortcut differs from the package')
            (backup / 'deployment.json').write_text(json.dumps(dict(
                source=record['source'], runtime_sha256=record['runtime_sha256'],
                gamefiles=len(asset_before), preserved_save_files=len(save_before),
                sd_root=str(sd), package=str(package), verified=True), indent=2) + '\n')
        if promoted_old:
            shutil.rmtree(previous)
        return backup
    except Exception:
        if activated:
            shutil.rmtree(target)
        if promoted_old and previous.exists():
            previous.rename(target)
        if activated:
            for shortcut in shortcuts:
                if shortcut.exists():
                    shortcut.unlink()
            with tarfile.open(backup / 'previous.tar.gz') as archive:
                for member in archive.getmembers():
                    if member.name in [SHORTCUT + '.port', SHORTCUT + '.notfound']:
                        archive.extract(member, sd, filter='data')
        raise
    finally:
        if staged.exists():
            shutil.rmtree(staged)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sd', type=Path, default=Path('/Volumes/MIYOO'))
    parser.add_argument('--package', type=Path, default=ROOT / 'artifacts/release/ufo50-miyoo-mini-development.zip')
    parser.add_argument('--gamefiles', type=Path)
    args = parser.parse_args()
    sd = args.sd.resolve()
    if not os.path.ismount(sd) or not os.access(sd, os.W_OK):
        parser.error('SD path must be a writable mounted filesystem')
    try:
        backup = deploy(sd, args.package.resolve(), args.gamefiles.resolve() if args.gamefiles else None,
                        ROOT / 'artifacts/sd-backups')
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        parser.error(str(error))
    subprocess.run(['sync'], check=True)
    print('Verified installation: ' + str(sd / GAME))
    print('Backup: ' + str(backup))
    print('Eject the card safely before removing it.')


if __name__ == '__main__':
    main()
