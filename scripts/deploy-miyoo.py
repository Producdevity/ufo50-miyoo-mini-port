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
from package import build_record, release_version

GAME = 'Roms/PORTS/Games/UFO50'
SHORTCUT = 'Roms/PORTS/Shortcuts/Action/UFO50'
SAVE = 'Saves/CurrentProfile/saves/UFO50'
CACHE = 'Roms/PORTS/Shortcuts/Shortcuts_cache6.db'
ARTWORK = 'Roms/PORTS/Imgs/UFO50.png'
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
    with zipfile.ZipFile(archive) as package:
        names = package.namelist()
        versioned = GAME + '/manifest.json' in names
        if len(names) != len(set(names)):
            raise ValueError('Duplicate package member')
        manifest_path = GAME + '/manifest.json' if versioned else 'manifest.json'
        documents = ['README.txt', 'THIRD_PARTY.txt'] if versioned else ['README.md', 'README.txt']
        allowed = {manifest_path, SHORTCUT + '.notfound', ARTWORK} | {
            GAME + '/' + name for name in ['bin/butterscotch', 'script.sh',
                'LICENSE', 'NOTICE', *documents]}
        if not versioned:
            allowed.update({'source.tar.gz', GAME + '/_required_files.txt'})
        if set(names) != allowed | {GAME + '/gamefiles/'}:
            raise ValueError('Unexpected or missing package member')
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
    record = json.loads((directory / manifest_path).read_text())
    binary = directory / GAME / 'bin/butterscotch'
    if record['source'] != source or record['target'] != 'armhf' or record['gamefiles_included']:
        raise ValueError('Wrong source, target or game-data boundary')
    if record['runtime_sha256'] != expected_record['runtime_sha256']:
        raise ValueError('Package differs from the verified local build')
    if sha256(binary) != record['runtime_sha256'] or inspect_arm32(binary) != record['elf']:
        raise ValueError('Runtime verification failed')
    if versioned:
        version = release_version(record['version'])
        source_name = f'ufo50-miyoo-mini-v{version}-source.tar.gz'
        expected_url = f'https://github.com/Producdevity/ufo50-miyoo-mini-port/releases/download/v{version}/{source_name}'
        if record['source_archive'] != source_name or record['source_url'] != expected_url:
            raise ValueError('Unexpected source archive reference')
        source_archive = archive.parent / source_name
    else:
        source_archive = directory / 'source.tar.gz'
    if sha256(source_archive) != record['source_archive_sha256']:
        raise ValueError('Source archive verification failed')
    source_files = [('port/artwork/UFO50.png', ARTWORK),
                    ('port/script.sh', GAME + '/script.sh'),
                    ('port/UFO50.notfound', SHORTCUT + '.notfound'),
                    ('LICENSE', GAME + '/LICENSE'), ('NOTICE', GAME + '/NOTICE'),
                    ('port/README.txt', GAME + '/README.txt')]
    if versioned:
        source_files.append(('licenses/THIRD_PARTY.txt', GAME + '/THIRD_PARTY.txt'))
    else:
        source_files.append(('README.md', GAME + '/README.md'))
    for source_name, packaged_name in source_files:
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
    artwork = sd / ARTWORK
    if artwork.is_symlink() or (artwork.exists() and not artwork.is_file()):
        raise ValueError('Artwork destination must be a regular file')
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
    next_artwork = artwork.with_name('.UFO50.png.next.' + stamp)
    shortcuts = [sd / (SHORTCUT + extension) for extension in ('.port', '.notfound')]
    activated = False
    promoted_old = False
    try:
        with tempfile.TemporaryDirectory(prefix='ufo50-package-check-') as temporary:
            unpacked = Path(temporary)
            record = unpack_package(package, unpacked)
            with tarfile.open(backup / 'previous.tar.gz', 'w:gz') as archive:
                for relative in [GAME, SAVE, SHORTCUT + '.port', SHORTCUT + '.notfound', ARTWORK, CACHE]:
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
            artwork.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(unpacked / ARTWORK, next_artwork)
            next_artwork.replace(artwork)
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
            if sha256(artwork) != sha256(unpacked / ARTWORK):
                raise ValueError('Installed artwork differs from the package')
            # Onion rebuilds this generated list so the new entry appears immediately.
            cache = sd / CACHE
            if cache.exists():
                cache.unlink()
            (backup / 'deployment.json').write_text(json.dumps(dict(
                source=record['source'], runtime_sha256=record['runtime_sha256'],
                artwork_sha256=sha256(artwork), gamefiles=len(asset_before), preserved_save_files=len(save_before),
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
            for installed in [*shortcuts, artwork]:
                if installed.exists():
                    installed.unlink()
            with tarfile.open(backup / 'previous.tar.gz') as archive:
                for member in archive.getmembers():
                    if member.name in [SHORTCUT + '.port', SHORTCUT + '.notfound', ARTWORK, CACHE]:
                        if not member.isfile():
                            raise ValueError('Unexpected backup member type')
                        destination = sd / member.name
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        with archive.extractfile(member) as source, destination.open('wb') as output:
                            shutil.copyfileobj(source, output)
        raise
    finally:
        if next_artwork.exists():
            next_artwork.unlink()
        if staged.exists():
            shutil.rmtree(staged)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sd', type=Path, default=Path('/Volumes/MIYOO'))
    version = release_version((ROOT / 'VERSION').read_text().strip())
    parser.add_argument('--package', type=Path, default=ROOT / f'artifacts/release/v{version}/ufo50-miyoo-mini-v{version}.zip')
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
