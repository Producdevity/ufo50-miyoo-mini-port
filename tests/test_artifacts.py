"""Reject incompatible target ABIs before any development ZIP can be produced."""
import struct
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from artifact import inspect_arm32
from package import check_performance_build


def elf_fixture(machine=40, flags=0x05000400, version='GLIBC_2.17', rpath=False):
    data = bytearray(480)
    data[:16] = b'\x7fELF\x01\x01\x01' + b'\0' * 9
    struct.pack_into('<HHIIIIIHHHHHH', data, 16, 2, machine, 1, 0, 52, 320,
                     flags, 52, 32, 1, 40, 4, 0)
    loader = b'/lib/ld-linux-armhf.so.3\0'
    struct.pack_into('<IIIIIIII', data, 52, 3, 84, 0, 0, len(loader), len(loader), 4, 1)
    data[84:84 + len(loader)] = loader
    strings = b'\0libSDL-1.2.so.0\0' + version.encode() + b'\0'
    data[176:176 + len(strings)] = strings
    struct.pack_into('<iI', data, 128, 1, 1)
    struct.pack_into('<iI', data, 136, 15 if rpath else 0, 1 if rpath else 0)
    struct.pack_into('<HHIII', data, 240, 1, 1, 1, 16, 0)
    struct.pack_into('<IHHII', data, 256, 0, 0, 2, strings.index(version.encode()), 0)
    for index, kind, offset, size, link, entry_size in [
            (1, 6, 128, 16, 2, 8), (2, 3, 176, len(strings), 0, 0),
            (3, 0x6ffffffe, 240, 32, 2, 0)]:
        struct.pack_into('<IIIIIIIIII', data, 320 + index * 40,
                         0, kind, 0, 0, offset, size, link, 0, 4, entry_size)
    return data


class Artifacts(unittest.TestCase):
    def inspect(self, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'runtime'
            path.write_bytes(data)
            return inspect_arm32(path)

    def test_target_metadata(self):
        self.assertEqual(self.inspect(elf_fixture())['max_glibc'], '2.17')

    def test_wrong_architecture(self):
        with self.assertRaises(ValueError):
            self.inspect(elf_fixture(machine=183))

    def test_soft_float(self):
        with self.assertRaises(ValueError):
            self.inspect(elf_fixture(flags=0x05000200))

    def test_new_glibc(self):
        with self.assertRaises(ValueError):
            self.inspect(elf_fixture(version='GLIBC_2.29'))

    def test_embedded_search_path(self):
        with self.assertRaises(ValueError):
            self.inspect(elf_fixture(rpath=True))

    def test_truncated_binary(self):
        with self.assertRaises(ValueError):
            self.inspect(elf_fixture()[:-1])


class PerformanceBuilds(unittest.TestCase):
    def record(self):
        return {'diagnostic_features': {key: 'OFF' for key in
            ['ENABLE_VM_TRACING', 'ENABLE_VM_GML_PROFILER', 'ENABLE_VM_OPCODE_PROFILER']},
            'interprocedural_optimization': True}

    def test_rejects_each_diagnostic_feature(self):
        check_performance_build(self.record())
        for feature in self.record()['diagnostic_features']:
            with self.subTest(feature=feature):
                record = self.record(); record['diagnostic_features'][feature] = 'ON'
                with self.assertRaisesRegex(ValueError, 'profiling'):
                    check_performance_build(record)

    def test_rejects_missing_build_settings(self):
        for key in ['diagnostic_features', 'interprocedural_optimization']:
            record = self.record(); del record[key]
            with self.assertRaises(ValueError):
                check_performance_build(record)
        record = self.record(); record['interprocedural_optimization'] = False
        with self.assertRaisesRegex(ValueError, 'optimization'):
            check_performance_build(record)


if __name__ == '__main__':
    unittest.main()
