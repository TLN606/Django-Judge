import glob
import os
import shutil
import tempfile
import unittest
from unittest import mock

from django.test import SimpleTestCase

from judge.service import JudgeService

HAS_GPP = shutil.which('g++') is not None

CPP_SUM = (
    '#include <iostream>\n'
    'int main(){long long a,b;std::cin>>a>>b;std::cout<<a+b;}\n'
)
CPP_DIFF = CPP_SUM.replace('a+b', 'a-b')
CPP_CRASH = 'int main(){ int *p = 0; *p = 1; return 0; }\n'
CPP_LOOP = 'int main(){ while(true){} }\n'
PY_SUM = 'a, b = map(int, input().split())\nprint(a + b)\n'


@unittest.skipUnless(HAS_GPP, 'g++ is not installed')
class JudgeCppTests(SimpleTestCase):

    def setUp(self):
        self.service = JudgeService()

    def test_accepted(self):
        result = self.service.judge(CPP_SUM, '1 2', '3')
        self.assertEqual(result.status, 'accepted')
        self.assertEqual(result.score, 100)

    def test_wrong_answer(self):
        result = self.service.judge(CPP_DIFF, '1 2', '3')
        self.assertEqual(result.status, 'wrong_answer')
        self.assertEqual(result.score, 0)

    def test_compile_error(self):
        result = self.service.judge('int main(){ return x; }', '', '')
        self.assertEqual(result.status, 'compile_error')
        self.assertIn('error', result.error_message)

    def test_runtime_error(self):
        result = self.service.judge(CPP_CRASH, '', '')
        self.assertEqual(result.status, 'runtime_error')

    def test_time_limit(self):
        result = self.service.judge(CPP_LOOP, '', '', time_limit=0.5)
        self.assertEqual(result.status, 'time_limit')

    def test_judge_all_returns_one_result_per_test(self):
        results = self.service.judge_all(
            CPP_SUM,
            [('1 2', '3'), ('10 20', '30'), ('1 1', '5')],
        )
        self.assertEqual(
            [r.status for r in results],
            ['accepted', 'accepted', 'wrong_answer'],
        )

    def test_compile_is_done_only_once(self):
        from judge import service as service_module

        real_get = service_module.get_compiler
        calls = []

        def counting_get(language):
            compiler = real_get(language)
            original = compiler.compile

            def compile_(source):
                calls.append(1)
                return original(source)

            compiler.compile = compile_
            return compiler

        with mock.patch.object(service_module, 'get_compiler', counting_get):
            self.service.judge_all(CPP_SUM, [('1 2', '3')] * 3)

        self.assertEqual(len(calls), 1)

    def test_temp_directory_is_removed(self):
        pattern = os.path.join(tempfile.gettempdir(), 'minijudge_*')
        before = set(glob.glob(pattern))
        self.service.judge(CPP_SUM, '1 2', '3')
        self.assertEqual(set(glob.glob(pattern)), before)


class JudgePythonTests(SimpleTestCase):

    def setUp(self):
        self.service = JudgeService()

    def test_python_accepted(self):
        result = self.service.judge(PY_SUM, '1 2', '3', language='python')
        self.assertEqual(result.status, 'accepted')

    def test_python_wrong_answer(self):
        result = self.service.judge(PY_SUM, '1 2', '4', language='python')
        self.assertEqual(result.status, 'wrong_answer')

    def test_python_syntax_error_is_compile_error(self):
        result = self.service.judge('def f(:\n', '', '', language='python')
        self.assertEqual(result.status, 'compile_error')

    def test_python_runtime_error(self):
        result = self.service.judge(
            'raise SystemExit(2)\n', '', '', language='python'
        )
        self.assertEqual(result.status, 'runtime_error')


class JudgeUnsupportedLanguageTests(SimpleTestCase):

    def test_unknown_language_is_system_error(self):
        results = JudgeService().judge_all(
            'x', [('', ''), ('', '')], language='java'
        )
        self.assertEqual([r.status for r in results], ['system_error'] * 2)
        self.assertIn('not supported', results[0].error_message)
