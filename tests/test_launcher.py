"""Exercise launcher cleanup without touching device settings or game assets."""
import os
import shutil
import signal
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class MiniLauncher(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='ufo50-launcher-')
        self.root = Path(self.temporary.name)
        for directory in ['game/bin', 'game/gamefiles', 'system/bin', 'tools']:
            (self.root / directory).mkdir(parents=True)
        shutil.copy2(ROOT / 'port/script.sh', self.root / 'game/script.sh')
        (self.root / 'game/gamefiles/data.win').write_bytes(b'fixture')
        (self.root / 'frequency').write_text('1200\n')
        (self.root / 'governor').write_text('ondemand\n')
        self.executable('tools/uname', '#!/bin/sh\nprintf "armv7l\\n"\n')
        self.executable('system/bin/cpuclock', '''#!/bin/sh
if [ "$#" -gt 0 ]; then printf '%s\\n' "$1" > "$TEST_ROOT/frequency"; fi
cat "$TEST_ROOT/frequency"
''')
        self.env = dict(os.environ, TEST_ROOT=str(self.root),
                        PATH=str(self.root / 'tools') + ':' + os.environ['PATH'],
                        UFO50_SAVE_DIR=str(self.root / 'saves'),
                        UFO50_SYSTEM_DIR=str(self.root / 'system'),
                        UFO50_GOVERNOR_FILE=str(self.root / 'governor'))

    def executable(self, name, text):
        path = self.root / name
        path.write_text(text)
        path.chmod(0o755)

    def tearDown(self):
        self.temporary.cleanup()

    def assert_restored(self):
        self.assertEqual((self.root / 'frequency').read_text().strip(), '1200')
        self.assertEqual((self.root / 'governor').read_text().strip(), 'ondemand')

    def test_exit_status_and_restore(self):
        self.executable('game/bin/butterscotch', '''#!/bin/sh
cat "$TEST_ROOT/frequency" > "$TEST_ROOT/during-frequency"
cat "$TEST_ROOT/governor" > "$TEST_ROOT/during-governor"
exit 7
''')
        result = subprocess.run(['sh', str(self.root / 'game/script.sh')], env=self.env, timeout=5)
        self.assertEqual(result.returncode, 7)
        self.assertEqual((self.root / 'during-frequency').read_text().strip(), '1500')
        self.assertEqual((self.root / 'during-governor').read_text().strip(), 'performance')
        self.assert_restored()

    def test_signal_stops_owned_child_and_restores(self):
        self.executable('game/bin/butterscotch', '''#!/bin/sh
printf '%s\\n' "$$" > "$TEST_ROOT/child"
while :; do sleep 0.05; done
''')
        process = subprocess.Popen(['sh', str(self.root / 'game/script.sh')], env=self.env)
        try:
            deadline = time.monotonic() + 3
            while not (self.root / 'child').exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue((self.root / 'child').exists())
            child = int((self.root / 'child').read_text())
            process.send_signal(signal.SIGTERM)
            self.assertEqual(process.wait(timeout=3), 143)
            with self.assertRaises(ProcessLookupError):
                os.kill(child, 0)
            self.assert_restored()
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()

    def test_invalid_clock_does_not_launch(self):
        self.executable('game/bin/butterscotch', '#!/bin/sh\ntouch "$TEST_ROOT/launched"\n')
        result = subprocess.run(['sh', str(self.root / 'game/script.sh')],
                                env=dict(self.env, UFO50_CPU_MHZ='9999'), timeout=5)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / 'launched').exists())
        self.assert_restored()
