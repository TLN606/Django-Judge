import os
import sys
import unittest

from django.test import SimpleTestCase

from judge.executor import ProgramExecutor

PY = sys.executable


class ProgramExecutorTests(SimpleTestCase):

    def setUp(self):
        self.executor = ProgramExecutor()

    def test_reads_stdin_and_returns_stdout(self):
        result = self.executor.execute(
            command=[PY, '-c', 'print(int(input())*2)'],
            input_data='21\n',
        )
        self.assertTrue(result.success)
        self.assertEqual(result.output.strip(), '42')
        self.assertEqual(result.return_code, 0)

    def test_nonzero_exit_is_runtime_failure(self):
        result = self.executor.execute(
            command=[PY, '-c', 'import sys; sys.exit(3)'],
        )
        self.assertFalse(result.success)
        self.assertEqual(result.return_code, 3)
        self.assertFalse(result.timed_out)

    def test_exception_text_goes_to_error_message(self):
        result = self.executor.execute(
            command=[PY, '-c', 'raise ValueError("boom")'],
        )
        self.assertFalse(result.success)
        self.assertIn('boom', result.error_message)

    def test_infinite_loop_times_out(self):
        result = self.executor.execute(
            command=[PY, '-c', 'while True: pass'],
            time_limit=0.5,
        )
        self.assertTrue(result.timed_out)
        self.assertFalse(result.success)
        self.assertGreaterEqual(result.execution_time, 0.4)

    def test_missing_executable(self):
        result = self.executor.execute(
            executable_path='/khong/ton/tai/solution.exe',
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, 'Executable not found.')

    def test_legacy_executable_path_argument(self):
        result = self.executor.execute(
            executable_path=sys.executable,
        )
        self.assertTrue(result.success)

    @unittest.skipUnless(os.name == 'posix', 'RLIMIT_AS chi co tren Linux/macOS')
    def test_memory_limit_stops_large_allocation(self):
        result = self.executor.execute(
            command=[PY, '-c', 'x = bytearray(600 * 1024 * 1024)'],
            time_limit=5,
            memory_limit_mb=128,
        )
        self.assertFalse(result.success)
