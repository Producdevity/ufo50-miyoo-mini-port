"""Exercise the release ZIP and separate source archive with a real Git fixture."""
import importlib.util
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import package
from artifact import inspect_arm32, sha256
from test_artifacts import elf_fixture
spec = importlib.util.spec_from_file_location('release_deploy', ROOT / 'scripts/deploy-miyoo.py')
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


class ReleasePackage(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='ufo50-release-test-')
        self.root = Path(self.temporary.name)
        self.repo = self.root / 'source'
        self.repo.mkdir()
        for name in ['port/script.sh', 'port/UFO50.notfound', 'port/README.txt',
                     'licenses/THIRD_PARTY.txt', 'LICENSE', 'NOTICE', 'README.md']:
            target = self.repo / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        (self.repo / 'docs/images').mkdir(parents=True)
        (self.repo / 'docs/images/gameplay.gif').write_bytes(b'preview fixture')
        subprocess.run(['git', 'init', '-q', '-b', 'master', str(self.repo)], check=True)
        subprocess.run(['git', '-C', str(self.repo), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.repo), '-c', 'user.name=Package Test',
                        '-c', 'user.email=package@example.invalid', 'commit', '-qm', 'fixture'], check=True)
        self.source = {'commit': subprocess.check_output(
            ['git', '-C', str(self.repo), 'rev-parse', 'HEAD'], text=True).strip(), 'dirty': False}
        self.binary = self.root / 'butterscotch'
        self.binary.write_bytes(elf_fixture())
        self.record = dict(target='armhf', source=self.source,
                           runtime_sha256=sha256(self.binary), elf=inspect_arm32(self.binary),
                           diagnostic_features={key: 'OFF' for key in
                               ['ENABLE_VM_TRACING', 'ENABLE_VM_GML_PROFILER', 'ENABLE_VM_OPCODE_PROFILER']},
                           interprocedural_optimization=True)
        self.output = self.root / 'release'
        self.output.mkdir()
        with patch.object(package, 'ROOT', self.repo), \
             patch.object(package, 'build_record', return_value=(self.binary, self.record)):
            self.archive = package.package('armhf', self.source, self.output, '0.1.0')

    def tearDown(self):
        self.temporary.cleanup()

    def unpack(self):
        with patch.object(deploy, 'ROOT', self.repo), \
             patch.object(deploy, 'source_state', return_value=self.source), \
             patch.object(deploy, 'build_record', return_value=(self.binary, self.record)):
            return deploy.unpack_package(self.archive, self.root / 'unpacked')

    def test_install_is_only_roms_and_source_is_separate(self):
        with zipfile.ZipFile(self.archive) as archive:
            names = archive.namelist()
            self.assertTrue(all(name.startswith('Roms/') for name in names))
            self.assertNotIn('source.tar.gz', names)
            self.assertFalse(any(name.endswith(('.gif', '.png', '.win', '.yytex')) for name in names))
            self.assertIn(deploy.GAME + '/README.txt', names)
            self.assertIn(deploy.GAME + '/THIRD_PARTY.txt', names)
            self.assertEqual(archive.getinfo(deploy.GAME + '/bin/butterscotch').external_attr >> 16 & 0o777, 0o755)
        record = self.unpack()
        self.assertEqual(record['version'], '0.1.0')
        with tarfile.open(self.output / record['source_archive']) as source:
            self.assertEqual(source.extractfile('docs/images/gameplay.gif').read(), b'preview fixture')
            self.assertEqual(source.extractfile('port/script.sh').read(), (self.repo / 'port/script.sh').read_bytes())

    def test_game_assets_are_rejected_before_deployment(self):
        with zipfile.ZipFile(self.archive, 'a') as archive:
            archive.writestr(deploy.GAME + '/gamefiles/data.win', b'private fixture')
        with self.assertRaisesRegex(ValueError, 'package member'):
            self.unpack()

    def test_altered_separate_source_is_rejected(self):
        source = self.output / 'ufo50-miyoo-mini-v0.1.0-source.tar.gz'
        with source.open('ab') as file:
            file.write(b'altered')
        with self.assertRaisesRegex(ValueError, 'Source archive verification'):
            self.unpack()

    def test_unsafe_versions_and_mixed_device_releases_are_rejected(self):
        for version in ['../0.1.0', 'v0.1.0', '01.1.0', '0.1.0/extra']:
            with self.subTest(version=version), self.assertRaises(ValueError):
                package.package('armhf', self.source, self.output, version)
        with self.assertRaisesRegex(ValueError, 'only the Miyoo Mini'):
            package.package('sp', self.source, self.output, '0.1.0')
