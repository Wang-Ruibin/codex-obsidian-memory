from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'plugins/codex-obsidian-memory'
SCRIPTS = PLUGIN / 'scripts'


class RuntimeLauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.runtime = self.root / 'private runtime'
        self.vault = self.root / 'vault'
        self.env = {**os.environ, 'CODEX_OBSIDIAN_RUNTIME_DIR': str(self.runtime),
                    'CODEX_OBSIDIAN_MEMORY_CONFIG': str(self.root / 'state/config.json')}
        if os.name == 'nt':
            self.launcher = [str(Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe'),
                             '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(SCRIPTS / 'memoryctl.ps1'), '-Action']
        else:
            self.launcher = ['/bin/sh', str(SCRIPTS / 'memoryctl.sh')]

    def tearDown(self):
        self.temp.cleanup()

    def run_launcher(self, *args, event=None, env=None):
        return subprocess.run([*self.launcher, *args], env=env or self.env, cwd=self.root,
                              input=json.dumps(event) if event else None, capture_output=True,
                              text=True, encoding='utf-8', timeout=30,
                              creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)

    def cached_python(self):
        self.runtime.mkdir(parents=True, exist_ok=True)
        (self.runtime / 'python-path.txt').write_text(sys.executable + '\n', encoding='utf-8')

    def no_python_path(self):
        directory = self.root / 'tools'
        directory.mkdir(exist_ok=True)
        if os.name != 'nt':
            for name in ('dirname', 'uname', 'mkdir', 'rmdir', 'mktemp', 'rm', 'mv', 'awk', 'tar', 'gzip', 'sha256sum', 'shasum'):
                path = shutil.which(name)
                if path:
                    (directory / name).symlink_to(path)
        return {**self.env, 'PATH': str(directory)}

    def test_prepare_reuses_python_and_is_idempotent(self):
        first = self.run_launcher('prepare-runtime')
        self.assertEqual(first.returncode, 0, first.stderr)
        selected = Path(first.stdout.strip())
        self.assertTrue(selected.is_file())
        self.assertFalse((self.runtime / 'python').exists())
        marker = (self.runtime / 'python-path.txt').read_bytes()
        second = self.run_launcher('prepare-runtime')
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(marker, (self.runtime / 'python-path.txt').read_bytes())
        self.assertFalse((self.runtime / 'prepare.lock').exists())

    def test_cached_runtime_runs_without_python_on_path_and_preserves_arguments(self):
        self.cached_python()
        env = self.no_python_path()
        initialized = self.run_launcher('init', '--local-only', '--vault', str(self.vault), '--no-writable-root', env=env)
        self.assertEqual(initialized.returncode, 0, initialized.stdout + initialized.stderr)
        work = self.root / 'project with spaces'
        work.mkdir()
        result = self.run_launcher('local-register', '--path', str(work), '--name', '本地项目', env=env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        registration = json.loads(result.stdout)
        self.assertEqual(registration['project']['name'], '本地项目')
        event = {'hook_event_name': 'SessionStart', 'cwd': str(work)}
        loaded = self.run_launcher('hook', event=event, env=env)
        self.assertEqual(loaded.returncode, 0, loaded.stderr)
        self.assertIn(registration['project']['project_id'], json.loads(loaded.stdout)['hookSpecificOutput']['additionalContext'])
        validation = self.run_launcher('validate', env=env)
        self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)

    def test_hook_without_runtime_fails_without_downloading_or_writing(self):
        result = self.run_launcher('hook', event={'hook_event_name': 'UserPromptSubmit', 'cwd': str(self.root)}, env=self.no_python_path())
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('prepare-runtime', result.stderr)
        self.assertFalse(self.runtime.exists())

    def test_failed_cli_exit_code_is_preserved(self):
        self.cached_python()
        result = self.run_launcher('invalid-command')
        self.assertEqual(result.returncode, 2, result.stderr)

    def test_validate_forwards_machine_readable_output_without_new_console(self):
        self.cached_python()
        initialized = self.run_launcher('init', '--local-only', '--vault', str(self.vault), '--no-writable-root')
        self.assertEqual(initialized.returncode, 0, initialized.stderr)
        report = self.run_launcher('validate')
        self.assertEqual(report.returncode, 0, report.stderr)
        self.assertEqual(json.loads(report.stdout)['duplicate_project_homes'], {})

    @unittest.skipIf(os.name == 'nt', 'POSIX download simulation; native Windows download is an integration check')
    def test_checksum_failure_cleans_download_and_lock(self):
        env = self.no_python_path()
        fake_curl = Path(env['PATH']) / 'curl'
        fake_curl.write_text('#!/bin/sh\nwhile [ "$#" -gt 0 ]; do if [ "$1" = "-o" ]; then shift; printf bad > "$1"; exit 0; fi; shift; done\n', encoding='utf-8')
        fake_curl.chmod(0o755)
        result = self.run_launcher('prepare-runtime', '--managed', env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('checksum mismatch', result.stderr)
        self.assertFalse((self.runtime / 'python-path.txt').exists())
        self.assertFalse((self.runtime / 'prepare.lock').exists())
        self.assertEqual(list(self.runtime.glob('.prepare.*')), [])

    @unittest.skipIf(os.name == 'nt', 'POSIX uv bootstrap simulation')
    def test_managed_setup_selects_private_interpreter_and_removes_bootstrap(self):
        env = self.no_python_path()
        tools_dir = Path(env['PATH'])
        (tools_dir / 'ln').symlink_to(shutil.which('ln'))
        machine = subprocess.check_output(['uname', '-m'], text=True).strip()
        cpu = 'aarch64' if machine in ('arm64', 'aarch64') else 'x86_64'
        target = cpu + ('-apple-darwin' if sys.platform == 'darwin' else '-unknown-linux-gnu')
        fixture = self.root / 'fixture'
        fixture.mkdir()
        uv_dir = fixture / ('uv-' + target)
        uv_dir.mkdir()
        uv = uv_dir / 'uv'
        uv.write_text('#!/bin/sh\nset -eu\ncase "$2" in\ninstall) mkdir -p "$UV_PYTHON_INSTALL_DIR/bin"; ln -s "$TEST_PYTHON" "$UV_PYTHON_INSTALL_DIR/bin/python3";;\nfind) printf "%s\\n" "$UV_PYTHON_INSTALL_DIR/bin/python3";;\nesac\n', encoding='utf-8')
        uv.chmod(0o755)
        archive = self.root / ('uv-' + target + '.tar.gz')
        with tarfile.open(archive, 'w:gz') as output:
            output.add(uv_dir, arcname=uv_dir.name)
        plugin = self.root / 'plugin'
        (plugin / 'scripts').mkdir(parents=True)
        (plugin / 'assets/runtime').mkdir(parents=True)
        shutil.copy2(SCRIPTS / 'memoryctl.sh', plugin / 'scripts/memoryctl.sh')
        (plugin / 'assets/runtime/uv-assets.txt').write_text('version fixture\n' + archive.name + ' ' + hashlib.sha256(archive.read_bytes()).hexdigest() + '\n', encoding='utf-8')
        (tools_dir / 'cp').symlink_to(shutil.which('cp'))
        curl = tools_dir / 'curl'
        curl.write_text('#!/bin/sh\nwhile [ "$#" -gt 0 ]; do if [ "$1" = "-o" ]; then shift; cp "$TEST_ARCHIVE" "$1"; exit 0; fi; shift; done\n', encoding='utf-8')
        curl.chmod(0o755)
        env.update(TEST_PYTHON=sys.executable, TEST_ARCHIVE=str(archive))
        self.launcher = ['/bin/sh', str(plugin / 'scripts/memoryctl.sh')]
        result = self.run_launcher('prepare-runtime', '--managed', env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(str(self.runtime / 'python'), result.stdout)
        self.assertEqual(list(self.runtime.glob('.prepare.*')), [])
        self.assertFalse((self.runtime / 'prepare.lock').exists())


if __name__ == '__main__':
    unittest.main()
