import io
import zipfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from config.testing import (
    PASSWORD, add_tests, make_classroom, make_problem, make_user,
)
from problems.models import Problem
from problems.services.package_exporter import (
    build_problem_package, build_problem_txt, safe_package_name,
)
from problems.services.package_importer import (
    ProblemPackageError, decode_text, parse_problem_file,
    parse_test_cases_file, validate_package,
)

PROBLEM_TXT = (
    'TITLE: Tong hai so\n\nDESCRIPTION:\nIn a + b.\n\n'
    'INPUT DESCRIPTION:\nHai so a, b.\n\n'
    'OUTPUT DESCRIPTION:\nMot so.\n\nCONSTRAINTS:\n|a|,|b| <= 1e9\n\n'
    'DIFFICULTY: easy\nTIME_LIMIT: 1\nMEMORY_LIMIT: 256\n'
)
INPUT_TXT = '2\n1 2\n10 20\n'
OUTPUT_TXT = '2\n3\n30\n'


class DecodeAndParseProblemTests(SimpleTestCase):

    def test_decode_utf8_with_bom(self):
        self.assertEqual(decode_text('﻿xin chào'.encode('utf-8')),
                         'xin chào')

    def test_decode_fallback_encoding(self):
        self.assertEqual(decode_text('é'.encode('cp1252')), 'é')

    def test_parse_valid_problem(self):
        data = parse_problem_file(PROBLEM_TXT)
        self.assertEqual(data['title'], 'Tong hai so')
        self.assertEqual(data['difficulty'], 'easy')
        self.assertEqual(data['time_limit'], 1.0)
        self.assertEqual(data['memory_limit'], 256)
        self.assertEqual(data['description'], 'In a + b.')

    def test_defaults_when_optional_metadata_missing(self):
        data = parse_problem_file('TITLE: X\nDESCRIPTION:\nmo ta\n')
        self.assertEqual(data['difficulty'], 'easy')
        self.assertEqual(data['time_limit'], 1.0)
        self.assertEqual(data['memory_limit'], 256)

    def test_invalid_problem_files(self):
        cases = {
            'empty': '',
            'no title': 'DESCRIPTION:\nabc\n',
            'bad difficulty': 'TITLE: X\nDIFFICULTY: legendary\n',
            'bad time': 'TITLE: X\nTIME_LIMIT: abc\n',
            'zero time': 'TITLE: X\nTIME_LIMIT: 0\n',
            'bad memory': 'TITLE: X\nMEMORY_LIMIT: abc\n',
            'zero memory': 'TITLE: X\nMEMORY_LIMIT: 0\n',
        }
        for name, content in cases.items():
            with self.subTest(name), self.assertRaises(ProblemPackageError):
                parse_problem_file(content)


class ParseTestCaseFileTests(SimpleTestCase):

    def test_simple_one_line_format(self):
        self.assertEqual(
            parse_test_cases_file('2\n1 2\n3 4\n', 'input.txt', 2),
            ['1 2', '3 4'])

    def test_marker_format_allows_multiline_cases(self):
        content = '2\n[TESTCASE 1]\n1\n2\n[TESTCASE 2]\n3\n4\n'
        self.assertEqual(
            parse_test_cases_file(content, 'input.txt', 2),
            ['1\n2', '3\n4'])

    def test_errors(self):
        bad = {
            'empty': ('', 2),
            'count not integer': ('abc\n1\n', 1),
            'count mismatch': ('3\n1\n2\n', 2),
            'wrong marker order': ('2\n[TESTCASE 2]\n1\n[TESTCASE 1]\n2\n', 2),
            'too few lines': ('3\n1\n2\n', 3),
        }
        for name, (content, expected) in bad.items():
            with self.subTest(name), self.assertRaises(ProblemPackageError):
                parse_test_cases_file(content, 'input.txt', expected)


class ValidatePackageTests(SimpleTestCase):

    def validate(self, problem=PROBLEM_TXT, inp=INPUT_TXT, out=OUTPUT_TXT):
        return validate_package(problem.encode(), inp.encode(), out.encode())

    def test_valid_package(self):
        data = self.validate()
        self.assertEqual(len(data.test_cases), 2)
        self.assertTrue(data.test_cases[0]['is_sample'])
        self.assertFalse(data.test_cases[1]['is_sample'])

    def test_invalid_packages(self):
        bad = {
            'no count in input': dict(inp='\n\n'),
            'count not int': dict(inp='abc\n1\n'),
            'count zero': dict(inp='0\n'),
            'empty expected output': dict(out='2\n3\n\n'),
        }
        for name, kwargs in bad.items():
            with self.subTest(name), self.assertRaises(ProblemPackageError):
                self.validate(**kwargs)


class ExporterTests(TestCase):

    def setUp(self):
        self.teacher = make_user('gv01', role='teacher')
        self.classroom = make_classroom(self.teacher)
        self.problem = make_problem(self.classroom, self.teacher)

    def test_safe_package_name(self):
        self.assertEqual(safe_package_name('a/b: c?'), 'a_b__c')
        self.assertEqual(safe_package_name('   '), 'problem')
        self.assertEqual(len(safe_package_name('x' * 200)), 80)

    def test_problem_txt_contains_metadata(self):
        text = build_problem_txt(self.problem)
        self.assertIn('TITLE: Tong hai so', text)
        self.assertIn('DIFFICULTY:', text)

    def test_cannot_export_without_test_cases(self):
        with self.assertRaises(ProblemPackageError):
            build_problem_package(self.problem)

    def test_export_contains_three_files(self):
        add_tests(self.problem)
        content, _ = build_problem_package(self.problem)
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            names = {n.rsplit('/', 1)[-1] for n in archive.namelist()}
        self.assertEqual(names, {'problem.txt', 'input.txt', 'output.txt'})


def make_zip(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return SimpleUploadedFile('goi.zip', buffer.getvalue())


class ImportViewTests(TestCase):

    def setUp(self):
        self.teacher = make_user('gv01', role='teacher')
        self.other = make_user('gv02', role='teacher')
        self.classroom = make_classroom(self.teacher)
        self.url = reverse('import_problem_package', args=[self.classroom.id])
        self.good = {
            'problem.txt': PROBLEM_TXT,
            'input.txt': INPUT_TXT,
            'output.txt': OUTPUT_TXT,
        }

    def login(self, user):
        self.assertTrue(
            self.client.login(username=user.username, password=PASSWORD))

    def test_import_zip_creates_draft_problem(self):
        self.login(self.teacher)
        self.client.post(self.url, {'package_zip': make_zip(self.good)})
        problem = Problem.objects.get()
        self.assertEqual(problem.status, 'draft')
        self.assertEqual(problem.test_cases.count(), 2)

    def test_import_folder_files(self):
        self.login(self.teacher)
        files = [
            SimpleUploadedFile(f'goi/{name}', content.encode())
            for name, content in self.good.items()
        ]
        self.client.post(self.url, {'package_folder': files})
        self.assertEqual(Problem.objects.count(), 1)

    def test_missing_file_is_rejected(self):
        self.login(self.teacher)
        del self.good['output.txt']
        self.client.post(self.url, {'package_zip': make_zip(self.good)})
        self.assertEqual(Problem.objects.count(), 0)

    def test_non_zip_upload_is_rejected(self):
        self.login(self.teacher)
        self.client.post(self.url, {
            'package_zip': SimpleUploadedFile('goi.txt', b'abc')})
        self.assertEqual(Problem.objects.count(), 0)

    def test_corrupted_zip_is_rejected(self):
        self.login(self.teacher)
        self.client.post(self.url, {
            'package_zip': SimpleUploadedFile('goi.zip', b'khong phai zip')})
        self.assertEqual(Problem.objects.count(), 0)

    def test_path_traversal_is_rejected(self):
        self.login(self.teacher)
        self.good['../problem.txt'] = 'x'
        self.client.post(self.url, {'package_zip': make_zip(self.good)})
        self.assertEqual(Problem.objects.count(), 0)

    def test_nothing_selected_shows_error(self):
        self.login(self.teacher)
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 200)

    def test_other_teacher_cannot_import(self):
        self.login(self.other)
        self.client.post(self.url, {'package_zip': make_zip(self.good)})
        self.assertEqual(Problem.objects.count(), 0)

    def test_get_renders_form(self):
        self.login(self.teacher)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_export_then_import_roundtrip(self):
        problem = make_problem(self.classroom, self.teacher)
        add_tests(problem)
        content, _ = build_problem_package(problem)
        self.login(self.teacher)
        self.client.post(self.url, {
            'package_zip': SimpleUploadedFile('goi.zip', content)})
        self.assertEqual(Problem.objects.count(), 2)
        copy = Problem.objects.exclude(pk=problem.pk).get()
        self.assertEqual(copy.test_cases.count(), 2)
