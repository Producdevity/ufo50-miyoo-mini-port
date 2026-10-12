"""Disk preflight rejects incomplete owned files without decoding them."""
import shutil
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class GameFileChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='ufo50-files-')
        cls.root = Path(cls.temporary.name)
        cls.executable = cls.root / 'check-files'
        subprocess.run([shutil.which('cc') or 'cc', '-std=c99', '-Wall', '-Wextra', '-Werror',
                        '-I' + str(ROOT / 'runtime/src'), str(ROOT / 'tests/native/game_files.c'),
                        str(ROOT / 'runtime/src/asset_path.c'), '-o', str(cls.executable)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def check(self, data, mode='form'):
        path = self.root / 'input'
        if data is None:
            path.unlink(missing_ok=True)
        else:
            path.write_bytes(data)
        args = [str(self.executable), mode, str(path)]
        if mode == 'texture':
            args += ['384', '216']
        return subprocess.run(args, timeout=3).returncode

    def test_form_missing_truncated_and_wrong_length(self):
        for data in [None, b'', b'FORM', b'FORM' + struct.pack('<I', 100) + b'partial',
                     b'NOPE' + struct.pack('<I', 4) + b'data',
                     b'FORM' + struct.pack('<I', 4) + b'dataextra']:
            with self.subTest(data=data):
                self.assertEqual(self.check(data), 1)
        self.assertEqual(self.check(b'FORM' + struct.pack('<I', 4) + b'data'), 0)

    def test_texture_missing_header_and_wrong_dimensions(self):
        header = b'2zoq' + struct.pack('<HHI', 384, 216, 1234)
        for data in [None, b'', header, header[:8], b'nope' + header[4:] + b'payload',
                     b'2zoq' + struct.pack('<HHI', 640, 480, 1234) + b'payload']:
            with self.subTest(data=data):
                self.assertEqual(self.check(data, 'texture'), 1)
        self.assertEqual(self.check(header + b'payload', 'texture'), 0)

    def test_case_mismatched_owned_paths_without_renaming(self):
        folder = self.root / 'Textures'
        folder.mkdir(exist_ok=True)
        actual = folder / 'PAGE.YYTEX'
        actual.write_bytes(b'owned-file fixture')
        lookup = self.root / 'textures/page.yytex'
        result = subprocess.run([str(self.executable), 'resolve', str(lookup)],
                                capture_output=True, text=True, timeout=3)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(Path(result.stdout.strip()).samefile(actual))
        self.assertEqual(actual.read_bytes(), b'owned-file fixture')
        relative = subprocess.run([str(self.executable), 'resolve', 'textures/page.yytex'],
                                  cwd=self.root, capture_output=True, text=True, timeout=3)
        self.assertEqual(relative.returncode, 0)
        self.assertTrue((self.root / relative.stdout.strip()).samefile(actual))
        self.assertEqual(subprocess.run([str(self.executable), 'resolve',
                                         str(folder / 'missing.yytex')], timeout=3).returncode, 1)

    def test_case_ambiguity_fails_but_exact_name_wins(self):
        folder = self.root / 'ambiguous'
        folder.mkdir(exist_ok=True)
        lower = folder / 'page.yytex'
        upper = folder / 'PAGE.YYTEX'
        lower.write_bytes(b'lower')
        upper.write_bytes(b'upper')
        if lower.samefile(upper):
            self.skipTest('Fixture filesystem is case-insensitive; also run on SP ext4')
        self.assertEqual(subprocess.run([str(self.executable), 'resolve',
                                         str(folder / 'Page.Yytex')], timeout=3).returncode, 1)
        result = subprocess.run([str(self.executable), 'resolve', str(lower)],
                                capture_output=True, text=True, timeout=3)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(Path(result.stdout.strip()).read_bytes(), b'lower')
