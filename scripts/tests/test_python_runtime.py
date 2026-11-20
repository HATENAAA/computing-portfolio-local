import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('python_runtime', Path(__file__).resolve().parents[1] / 'python_runtime.py')
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


class RuntimeSetupTests(unittest.TestCase):
    def test_existing_python_skips_all_network_setup(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(runtime, 'find_existing', return_value='/local/python3.12'), patch.object(runtime, 'bootstrap') as download:
            self.assertEqual(runtime.ensure_python312(Path(temp), True), '/local/python3.12')
            download.assert_not_called()
            self.assertFalse((Path(temp) / '.tools').exists())

    def test_missing_python_check_does_not_download(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(runtime, 'find_existing', return_value=None), patch.object(runtime, 'bootstrap') as download:
            with self.assertRaisesRegex(RuntimeError, 'Python 3.12'):
                runtime.ensure_python312(Path(temp))
            download.assert_not_called()

    def test_failed_or_wrong_version_candidate_is_skipped(self):
        results = [subprocess.CompletedProcess([], 1, '', ''), subprocess.CompletedProcess([], 0, '{"version":[3,11]}', ''), subprocess.CompletedProcess([], 0, '{"version":[3,12],"base":"/good"}', '')]
        with patch.object(runtime, 'candidates', return_value=iter(['/broken', '/old', '/good'])), patch.object(runtime.subprocess, 'run', side_effect=results):
            self.assertEqual(runtime.find_existing(Path('/unused')), '/good')

    def test_download_is_validated_before_reporting_success(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(runtime, 'find_existing', side_effect=[None, '/downloaded/python3.12']), patch.object(runtime, 'bootstrap') as download:
            self.assertEqual(runtime.ensure_python312(Path(temp), True), '/downloaded/python3.12')
            download.assert_called_once()

    def test_process_timeout_stops_wait_and_keeps_diagnostics(self):
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / 'setup.log'
            started = time.monotonic()
            with self.assertRaisesRegex(RuntimeError, '超时'):
                runtime.run_step([sys.executable, '-c', 'import time;print("started",flush=True);time.sleep(30)'], log, '测试下载', 0.3)
            self.assertLess(time.monotonic() - started, 3)
            self.assertIn('started', log.read_text())

    def test_nonzero_exit_reports_actual_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(RuntimeError, 'network-unavailable'):
                runtime.run_step([sys.executable, '-c', 'import sys;print("network-unavailable");sys.exit(7)'], Path(temp) / 'setup.log', '测试下载', 3)

    def test_failed_download_uses_alternative_official_source(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(runtime.Path, 'home', return_value=Path(temp) / 'home'), patch.object(runtime.shutil, 'which', side_effect=lambda name: '/fake/curl' if name == 'curl' else None):
            calls = []
            def step(args, log, label, timeout, env=None, progress_file=None):
                calls.append((args, timeout, env))
                if progress_file:
                    if len(calls) == 1:
                        progress_file.write_text('incomplete')
                        raise RuntimeError('primary source unavailable')
                    progress_file.write_text('#!/bin/sh\nexit 0\n')
                elif args[0] == '/bin/sh':
                    (Path(temp) / '.tools/bin/uv').write_text('test uv')
            with patch.object(runtime, 'run_step', side_effect=step):
                runtime.bootstrap(Path(temp))
            self.assertEqual([x[0][-1] for x in calls[:2]], list(runtime.INSTALLERS))
            self.assertFalse((Path(temp) / '.tools/uv-install.sh.partial').exists())
            self.assertEqual([x[1] for x in calls], [45, 45, 180, 300])
            self.assertEqual(calls[-1][2]['UV_HTTP_RETRIES'], '1')

    def test_all_download_sources_failing_returns_clear_error(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(runtime.Path, 'home', return_value=Path(temp) / 'home'), patch.object(runtime.shutil, 'which', side_effect=lambda name: '/fake/curl' if name == 'curl' else None), patch.object(runtime, 'run_step', side_effect=RuntimeError('offline')) as step:
            with self.assertRaisesRegex(RuntimeError, '两个官方来源'):
                runtime.bootstrap(Path(temp))
            self.assertEqual(step.call_count, 2)


if __name__ == '__main__':
    unittest.main()
