import os
import shutil
import unittest

from django.test import SimpleTestCase

from judge.compiler import (
    CppCompiler,
    PythonCompiler,
    get_compiler,
)

HAS_GPP = shutil.which('g++') is not None

HELLO_CPP = '#include <iostream>\nint main(){std::cout<<1;}\n'


def cleanup(result):
    if result.work_dir:
        shutil.rmtree(result.work_dir, ignore_errors=True)


@unittest.skipUnless(HAS_GPP, 'g++ is not installed')
class CppCompilerTests(SimpleTestCase):

    def test_valid_code_compiles(self):
        result = CppCompiler().compile(HELLO_CPP)
        self.addCleanup(cleanup, result)
        self.assertTrue(result.success)
        self.assertTrue(os.path.exists(result.executable_path))
        self.assertEqual(result.command, [result.executable_path])

    def test_syntax_error_reports_message(self):
        result = CppCompiler().compile('int main(){ return x; }')
        self.addCleanup(cleanup, result)
        self.assertFalse(result.success)
        self.assertIn('error', result.error_message)


class CppCompilerMissingToolTests(SimpleTestCase):

    def test_missing_compiler_gives_clear_message(self):
        compiler = CppCompiler()
        compiler.compiler = 'g++-khong-ton-tai-xyz'
        result = compiler.compile(HELLO_CPP)
        self.addCleanup(cleanup, result)
        self.assertFalse(result.success)
        self.assertIn('not found', result.error_message)


class PythonCompilerTests(SimpleTestCase):

    def test_valid_code_is_accepted(self):
        result = PythonCompiler().compile('print(1)\n')
        self.addCleanup(cleanup, result)
        self.assertTrue(result.success)
        self.assertEqual(len(result.command), 2)

    def test_syntax_error_is_reported(self):
        result = PythonCompiler().compile('def f(:\n')
        self.addCleanup(cleanup, result)
        self.assertFalse(result.success)
        self.assertTrue(result.error_message)


class GetCompilerTests(SimpleTestCase):

    def test_known_languages(self):
        self.assertIsInstance(get_compiler('cpp'), CppCompiler)
        self.assertIsInstance(get_compiler('python'), PythonCompiler)

    def test_unknown_language_returns_none(self):
        self.assertIsNone(get_compiler('java'))
