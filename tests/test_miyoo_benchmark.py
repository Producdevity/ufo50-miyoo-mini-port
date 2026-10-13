"""Exercise the bounded test driver and its data boundaries in a fake card."""
import importlib.util
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import test_launcher

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


setup = module('test_setup', 'setup-miyoo-tests.py')
summary = module('test_summary', 'summarize-miyoo-tests.py')


class TestDriver(unittest.TestCase):
    def setUp(self):
        self.fixture = test_launcher.MiniLauncher('test_exit_status_and_restore')
        self.fixture.setUp()
        self.root = self.fixture.root
        self.env = dict(self.fixture.env, UFO50_TEST_DIR=str(self.root / 'runs'))
        self.game = self.root / 'game'
        shutil.copy2(ROOT / 'port/diagnostics/miyoo-fps-test.sh', self.game / 'miyoo-fps-test.sh')
        (self.game / 'miyoo-tests').mkdir()
        for index in [18, 29, 34]:
            (self.game / f'miyoo-tests/input-{index}.json').write_text('{}')
        (self.game / 'miyoo-tests/config.json').write_text('{"scale":1,"scanlines":2}')
        self.fixture.executable('tools/sha256sum', '#!/bin/sh\nexec shasum -a 256 "$@"\n')
        self.normal_saves = self.root / 'saves'
        self.normal_saves.mkdir()
        (self.normal_saves / 'save1.ufo').write_bytes(b'keep me')

    def tearDown(self):
        self.fixture.tearDown()

    def run_driver(self, **environment):
        return subprocess.run(['sh', str(self.game / 'miyoo-fps-test.sh')],
                              env=dict(self.env, **environment), timeout=8)

    def test_three_runs_are_isolated_and_bounded(self):
        self.fixture.executable('game/bin/butterscotch', '''#!/bin/sh
printf '%s\\n' "$@" > "$UFO50_SAVE_DIR/arguments"
printf '%s\\n' "$UFO50_KEYBOARD_PLAYBACK" > "$UFO50_SAVE_DIR/playback"
while [ "$#" -gt 0 ]; do
    if [ "$1" = --dump-frame-json-file ]; then shift; printf '{}' > "$1"; break; fi
    shift
done
echo 'Startup: first frame presented'
echo 'Bye! :3'
''')
        self.assertEqual(self.run_driver().returncode, 0)
        run = next((self.root / 'runs').iterdir())
        self.assertTrue((run / 'complete').is_file())
        for index in [18, 29, 34]:
            case = run / f'game-{index}'
            args = (case / 'saves/arguments').read_text()
            self.assertIn('--exit-at-frame\n5000', args)
            self.assertIn('--seed\n1234', args)
            self.assertIn(str(case / 'saves'), args)
            self.assertEqual((case / 'saves/playback').read_text().strip(), '1')
            self.assertEqual(json.loads((case / 'saves/config.json').read_text()), dict(scale=1, scanlines=2))
        self.assertEqual((self.normal_saves / 'save1.ufo').read_bytes(), b'keep me')
        self.fixture.assert_restored()

    def test_timeout_stops_own_game_and_restores_clock(self):
        self.fixture.executable('game/bin/butterscotch', '''#!/bin/sh
printf '%s\\n' "$$" > "$TEST_ROOT/child"
echo 'Startup: first frame presented'
while :; do sleep 0.05; done
''')
        self.assertNotEqual(self.run_driver(UFO50_TEST_TIMEOUT='1').returncode, 0)
        run = next((self.root / 'runs').iterdir())
        self.assertFalse((run / 'complete').exists())
        self.assertTrue((run / 'game-18/timed-out').exists())
        with self.assertRaises(ProcessLookupError):
            os.kill(int((self.root / 'child').read_text()), 0)
        self.fixture.assert_restored()
        self.assertEqual((self.normal_saves / 'save1.ufo').read_bytes(), b'keep me')

    def test_signal_cleans_up_the_owned_launcher_chain(self):
        self.fixture.executable('game/bin/butterscotch', '''#!/bin/sh
printf '%s\\n' "$$" > "$TEST_ROOT/child"
echo 'Startup: first frame presented'
while :; do sleep 0.05; done
''')
        process = subprocess.Popen(['sh', str(self.game / 'miyoo-fps-test.sh')], env=self.env)
        try:
            deadline = time.monotonic() + 3
            while not (self.root / 'child').exists() and time.monotonic() < deadline:
                time.sleep(.01)
            self.assertTrue((self.root / 'child').exists())
            child = int((self.root / 'child').read_text())
            process.send_signal(signal.SIGTERM)
            self.assertEqual(process.wait(timeout=4), 143)
            with self.assertRaises(ProcessLookupError):
                os.kill(child, 0)
            self.fixture.assert_restored()
        finally:
            if process.poll() is None:
                process.kill(); process.wait()


class TestInstallation(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='ufo50-test-card-')
        self.root = Path(self.temporary.name)
        self.sd = self.root / 'card'
        game = self.sd / setup.deploy.GAME
        for directory in [game / 'bin', game / 'gamefiles', self.sd / setup.deploy.SAVE,
                          self.sd / 'Emu/PORTS', self.sd / Path(setup.SHORTCUT).parent]:
            directory.mkdir(parents=True, exist_ok=True)
        (game / 'bin/butterscotch').write_bytes(b'fixture runtime')
        (game / 'script.sh').write_bytes(b'original launcher')
        (game / 'gamefiles/data.win').write_bytes(b'owned fixture')
        (self.sd / setup.deploy.SAVE / 'save1.ufo').write_bytes(b'original save')
        (self.sd / 'Emu/PORTS/launch_standalone.sh').write_bytes(b'fixture')
        (self.sd / setup.deploy.CACHE).write_bytes(b'original cache')
        self.runtime = setup.sha256(game / 'bin/butterscotch')

    def tearDown(self):
        self.temporary.cleanup()

    def test_installs_only_diagnostic_files_with_protected_recordings(self):
        saves = setup.deploy.manifest(self.sd / setup.deploy.SAVE)
        assets = setup.deploy.manifest(self.sd / setup.deploy.GAME / 'gamefiles')
        backup = setup.install(self.sd, self.runtime, self.root / 'backup')
        self.assertTrue((backup / 'previous.tar.gz').is_file())
        self.assertTrue((self.sd / setup.SHORTCUT).is_file())
        self.assertEqual(setup.deploy.manifest(self.sd / setup.deploy.SAVE), saves)
        self.assertEqual(setup.deploy.manifest(self.sd / setup.deploy.GAME / 'gamefiles'), assets)
        self.assertEqual((self.sd / setup.deploy.GAME / 'script.sh').read_bytes(), b'original launcher')
        for index in [18, 29, 34]:
            plan = json.loads((self.sd / setup.INPUTS / f'input-{index}.json').read_text())
            self.assertEqual(plan['5000'], dict(keysPressed=[], keysReleased=[]))
        self.assertFalse((self.sd / setup.deploy.CACHE).exists())

    def test_post_install_failure_restores_previous_helpers_and_cache(self):
        (self.sd / setup.SCRIPT).write_bytes(b'old helper')
        (self.sd / setup.SHORTCUT).write_bytes(b'old test shortcut')
        original = setup.deploy.manifest
        count = 0
        def fail(path):
            nonlocal count
            if path == self.sd / setup.INPUTS:
                count += 1
                if count == 1:
                    raise ValueError('injected verification failure')
            return original(path)
        with patch.object(setup.deploy, 'manifest', fail):
            with self.assertRaisesRegex(ValueError, 'injected'):
                setup.install(self.sd, self.runtime, self.root / 'backup')
        self.assertEqual((self.sd / setup.SCRIPT).read_bytes(), b'old helper')
        self.assertEqual((self.sd / setup.SHORTCUT).read_bytes(), b'old test shortcut')
        self.assertEqual((self.sd / setup.deploy.CACHE).read_bytes(), b'original cache')
        self.assertEqual((self.sd / setup.deploy.SAVE / 'save1.ufo').read_bytes(), b'original save')


class TestSummary(unittest.TestCase):
    def test_counts_long_gaps_and_rejects_unprotected_playback(self):
        with tempfile.TemporaryDirectory(prefix='ufo50-test-summary-') as temporary:
            root = Path(temporary)
            (root / 'complete').touch()
            (root / 'runtime.sha256').write_text('0' * 64 + ' runtime\n')
            for index in [18, 29, 34]:
                case = root / f'game-{index}'
                (case / 'saves/logs').mkdir(parents=True)
                (case / 'plan.json').write_text(json.dumps(dict(index=index)))
                (case / 'exit-status').write_text('0')
                titles = ['fixture'] * 51
                state = dict(frame=4999, room=dict(name='fixtureRoom'),
                             globalVariables=dict(currGame=index, scanlines=2, scale=1, mGameTitle=titles))
                (case / 'state.json').write_text(json.dumps(state))
                (case / 'saves/logs/run.log').write_text(
                    'Perf: frame=3500 seconds=2 steps=120 presents=60 work_ms=8 interval_max_ms=83.333 long_intervals=2\n'
                    'Audio output: callbacks=1 frames=1024 nonzero_samples=2048 peak=0.75\nBye! :3\nGame exited: 0\n')
            result = summary.summarize(root)
            self.assertEqual(result['runs'][0]['presentations_per_second'], 30)
            self.assertEqual(result['runs'][0]['long_intervals'], 2)
            self.assertEqual(result['runs'][0]['max_interval_ms'], 83.333)
            with (root / 'game-18/saves/logs/run.log').open('a') as f:
                f.write('Playback ended\n')
            with self.assertRaisesRegex(ValueError, 'protected replay'):
                summary.summarize(root)
