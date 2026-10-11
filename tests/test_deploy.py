"""Check installation preservation and rollback in a temporary card fixture."""
import importlib.util
import shutil
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('mini_deploy', ROOT / 'scripts/deploy-miyoo.py')
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


class Deployment(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='ufo50-deploy-test-')
        self.root = Path(self.temporary.name)
        self.sd = self.root / 'card'
        self.target = self.sd / deploy.GAME
        self.saves = self.sd / deploy.SAVE
        for directory in [self.sd / 'Emu/PORTS', self.target / 'gamefiles', self.saves,
                          self.sd / Path(deploy.SHORTCUT).parent]:
            directory.mkdir(parents=True, exist_ok=True)
        (self.sd / 'Emu/PORTS/launch_standalone.sh').write_text('fixture')
        (self.target / 'gamefiles/data.win').write_bytes(b'owned fixture')
        (self.target / 'old-runtime').write_bytes(b'old')
        (self.saves / 'save1.ufo').write_bytes(b'keep this save')
        (self.sd / (deploy.SHORTCUT + '.notfound')).write_bytes(b'old shortcut')
        (self.sd / deploy.CACHE).write_bytes(b'old list cache')
        self.save_before = deploy.manifest(self.saves)
        self.asset_before = deploy.manifest(self.target / 'gamefiles')

    def tearDown(self):
        self.temporary.cleanup()

    def package_fixture(self, _, directory):
        game = directory / deploy.GAME
        (game / 'bin').mkdir(parents=True)
        (game / 'bin/butterscotch').write_bytes(b'new runtime')
        (game / 'script.sh').write_bytes(b'new launcher')
        shortcut = directory / (deploy.SHORTCUT + '.notfound')
        shortcut.parent.mkdir(parents=True)
        shortcut.write_bytes(b'new shortcut')
        return dict(source={'commit': 'fixture'}, runtime_sha256=deploy.sha256(game / 'bin/butterscotch'))

    def run_deploy(self):
        with patch.object(deploy, 'unpack_package', self.package_fixture):
            return deploy.deploy(self.sd, self.root / 'fixture.zip', None, self.root / 'backups')

    def test_preserves_assets_and_saves_with_recoverable_backup(self):
        backup = self.run_deploy()
        self.assertEqual(deploy.manifest(self.saves), self.save_before)
        self.assertEqual(deploy.manifest(self.target / 'gamefiles'), self.asset_before)
        self.assertEqual((self.target / 'bin/butterscotch').read_bytes(), b'new runtime')
        self.assertTrue((self.sd / (deploy.SHORTCUT + '.port')).is_file())
        self.assertFalse((self.sd / deploy.CACHE).exists())
        with tarfile.open(backup / 'previous.tar.gz') as archive:
            self.assertEqual(archive.extractfile(deploy.CACHE).read(), b'old list cache')
            self.assertEqual(archive.extractfile(deploy.SAVE + '/save1.ufo').read(), b'keep this save')
            self.assertEqual(archive.extractfile(deploy.GAME + '/old-runtime').read(), b'old')

    def test_verification_failure_rolls_back_installation_and_shortcut(self):
        original_manifest = deploy.manifest
        checks = 0

        def failing_manifest(directory):
            nonlocal checks
            if directory == self.target / 'gamefiles':
                checks += 1
                if checks == 2:
                    raise ValueError('injected post-promotion failure')
            return original_manifest(directory)

        with patch.object(deploy, 'manifest', failing_manifest):
            with self.assertRaisesRegex(ValueError, 'injected'):
                self.run_deploy()
        self.assertEqual((self.target / 'old-runtime').read_bytes(), b'old')
        self.assertEqual((self.sd / (deploy.SHORTCUT + '.notfound')).read_bytes(), b'old shortcut')
        self.assertFalse((self.sd / (deploy.SHORTCUT + '.port')).exists())
        self.assertEqual((self.sd / deploy.CACHE).read_bytes(), b'old list cache')
        self.assertEqual(deploy.manifest(self.saves), self.save_before)
        self.assertEqual(deploy.manifest(self.target / 'gamefiles'), self.asset_before)

    def test_refuses_missing_assets_before_writing(self):
        shutil.rmtree(self.target)
        with self.assertRaisesRegex(ValueError, 'Supply owned assets'):
            self.run_deploy()
        self.assertFalse((self.root / 'backups').exists())
        self.assertFalse(self.target.exists())
        self.assertEqual(deploy.manifest(self.saves), self.save_before)

    def test_refuses_replacing_owned_game_files(self):
        with self.assertRaisesRegex(ValueError, 'Existing gamefiles'):
            deploy.deploy(self.sd, self.root / 'fixture.zip', self.root, self.root / 'backups')
        self.assertFalse((self.root / 'backups').exists())
        self.assertEqual(deploy.manifest(self.target / 'gamefiles'), self.asset_before)
