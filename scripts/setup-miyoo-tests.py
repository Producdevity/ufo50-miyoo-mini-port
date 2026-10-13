#!/usr/bin/env python3
"""Install a separate bounded FPS test entry on a card with the current release."""
import argparse
import datetime
import importlib.util
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path
from artifact import ROOT, sha256, source_state
from package import build_record

spec = importlib.util.spec_from_file_location('mini_deploy', ROOT / 'scripts/deploy-miyoo.py')
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)
spec = importlib.util.spec_from_file_location('library', ROOT / 'scripts/test-library.py')
library = importlib.util.module_from_spec(spec)
spec.loader.exec_module(library)

SHORTCUT = 'Roms/PORTS/Shortcuts/Action/UFO50-FPS-Test.port'
SCRIPT = deploy.GAME + '/miyoo-fps-test.sh'
INPUTS = deploy.GAME + '/miyoo-tests'


def install(sd, runtime_sha256, backup_root):
    game = sd / deploy.GAME
    if not (sd / 'Emu/PORTS/launch_standalone.sh').is_file():
        raise ValueError('Onion Ports Collection launcher is missing')
    if sha256(game / 'bin/butterscotch') != runtime_sha256:
        raise ValueError('Install the current verified release before adding its test entry')
    if not (game / 'gamefiles/data.win').is_file():
        raise ValueError('Owned game files are missing')
    assets = deploy.manifest(game / 'gamefiles')
    saves = deploy.manifest(sd / deploy.SAVE)
    normal_script = sha256(game / 'script.sh')
    affected = [SCRIPT, INPUTS, SHORTCUT, deploy.CACHE]
    for relative in affected:
        if (sd / relative).is_symlink():
            raise ValueError('Symlink at a diagnostic destination')
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '-tests-' + str(os.getpid())
    backup = backup_root / stamp
    backup.mkdir(parents=True, exist_ok=False)
    with tarfile.open(backup / 'previous.tar.gz', 'w:gz') as archive:
        for relative in [deploy.GAME, deploy.SAVE, SHORTCUT, deploy.CACHE]:
            if (sd / relative).exists():
                archive.add(sd / relative, arcname=relative)
    (backup / 'before.json').write_text(json.dumps(dict(gamefiles=assets, saves=saves), indent=2) + '\n')
    try:
        with tempfile.TemporaryDirectory(prefix='ufo50-mini-tests-') as directory:
            stage = Path(directory)
            (stage / 'inputs').mkdir()
            for index in [18, 29, 34]:
                plan = library.input_plan(index)
                plan['5000'] = dict(keysPressed=[], keysReleased=[])
                (stage / f'inputs/input-{index}.json').write_text(json.dumps(plan, indent=2) + '\n')
            (stage / 'inputs/config.json').write_text('{"scale":1,"scanlines":2}\n')
            if (sd / INPUTS).exists():
                shutil.rmtree(sd / INPUTS)
            shutil.copytree(stage / 'inputs', sd / INPUTS)
            for source, relative in [('miyoo-fps-test.sh', SCRIPT), ('miyoo-fps-test.port', SHORTCUT)]:
                target = sd / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                next_file = target.with_name(target.name + '.next')
                shutil.copy2(ROOT / 'port/diagnostics' / source, next_file)
                next_file.chmod(0o755)
                next_file.replace(target)
                if sha256(target) != sha256(ROOT / 'port/diagnostics' / source):
                    raise ValueError('Installed test script differs')
            if deploy.manifest(sd / INPUTS) != deploy.manifest(stage / 'inputs'):
                raise ValueError('Installed recordings differ')
            if (deploy.manifest(game / 'gamefiles') != assets or
                    deploy.manifest(sd / deploy.SAVE) != saves or
                    sha256(game / 'bin/butterscotch') != runtime_sha256 or
                    sha256(game / 'script.sh') != normal_script):
                raise ValueError('Normal port, owned assets or saves changed')
            if (sd / deploy.CACHE).exists():
                (sd / deploy.CACHE).unlink()
            (backup / 'deployment.json').write_text(json.dumps(dict(
                runtime_sha256=runtime_sha256, preserved_gamefiles=len(assets),
                preserved_save_files=len(saves), shortcut=SHORTCUT,
                isolated_test_saves='Saves/CurrentProfile/saves/UFO50-tests', verified=True), indent=2) + '\n')
        return backup
    except Exception:
        for relative in [SCRIPT, SHORTCUT]:
            staged = (sd / relative).with_name(Path(relative).name + '.next')
            if staged.exists():
                staged.unlink()
        for relative in affected:
            path = sd / relative
            if path.is_dir():
                shutil.rmtree(path)
            elif path.exists():
                path.unlink()
        with tarfile.open(backup / 'previous.tar.gz') as archive:
            for member in archive:
                if not any(member.name == p or member.name.startswith(p + '/') for p in affected):
                    continue
                destination = sd / member.name
                if member.isdir():
                    destination.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with archive.extractfile(member) as src, destination.open('wb') as dst:
                        shutil.copyfileobj(src, dst)
                    destination.chmod(member.mode)
                else:
                    raise ValueError('Unsupported diagnostic backup member')
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sd', type=Path, default=Path('/Volumes/MIYOO'))
    args = parser.parse_args()
    sd = args.sd.resolve()
    if not os.path.ismount(sd) or not os.access(sd, os.W_OK):
        parser.error('SD path must be a writable mounted filesystem')
    source = source_state()
    if source['dirty']:
        parser.error('Use the clean release checkout')
    _, record = build_record('armhf', source)
    backup = install(sd, record['runtime_sha256'], ROOT / 'artifacts/sd-backups')
    subprocess.run(['sync'], check=True)
    print('Installed Action → UFO50-FPS-Test. Backup: ' + str(backup))
    print('Eject safely, launch that entry on the Mini once, then remount the card to collect results.')


if __name__ == '__main__':
    main()
