from django.test import TestCase
from django.urls import reverse

from config.testing import (
    PASSWORD, add_tests, join, make_classroom, make_problem, make_user,
)
from problems.forms import ProblemForm, TestCaseForm
from problems.models import Problem, ProblemAttempt, TestCase as Case


def problem_post(title, cases=(('1 2', '3'),), existing=()):
    """Dữ liệu POST gồm form bài tập + formset Test Case (prefix test_cases)."""
    data = {
        'title': title, 'description': 'Mo ta',
        'input_description': '', 'output_description': '',
        'constraints': '', 'difficulty': 'easy',
        'time_limit': 1, 'memory_limit': 256,
        'test_cases-TOTAL_FORMS': len(existing) + len(cases),
        'test_cases-INITIAL_FORMS': len(existing),
        'test_cases-MIN_NUM_FORMS': 0,
        'test_cases-MAX_NUM_FORMS': 1000,
    }
    for i, (pk, inp, out) in enumerate(existing):
        data[f'test_cases-{i}-id'] = pk
        data[f'test_cases-{i}-input_data'] = inp
        data[f'test_cases-{i}-expected_output'] = out
    for j, (inp, out) in enumerate(cases):
        i = len(existing) + j
        data[f'test_cases-{i}-input_data'] = inp
        data[f'test_cases-{i}-expected_output'] = out
    return data


class ProblemTestBase(TestCase):

    def setUp(self):
        self.teacher = make_user('gv01', role='teacher')
        self.other_teacher = make_user('gv02', role='teacher')
        self.student = make_user('sv01')
        self.classroom = make_classroom(self.teacher)
        join(self.classroom, self.student)

    def login(self, user):
        self.assertTrue(
            self.client.login(username=user.username, password=PASSWORD))


class ProblemModelTests(ProblemTestBase):

    def test_str_returns_title(self):
        problem = make_problem(self.classroom, self.teacher)
        self.assertIn('Tong hai so', str(problem))

    def test_attempt_can_submit_depends_on_status(self):
        problem = make_problem(self.classroom, self.teacher)
        attempt = ProblemAttempt.objects.create(
            problem=problem, student=self.student)
        self.assertTrue(attempt.can_submit)
        attempt.status = 'locked'
        self.assertFalse(attempt.can_submit)
        self.assertIn('sv01', str(attempt))

    def test_one_attempt_per_student_and_problem(self):
        from django.db import IntegrityError, transaction
        problem = make_problem(self.classroom, self.teacher)
        ProblemAttempt.objects.create(problem=problem, student=self.student)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ProblemAttempt.objects.create(
                problem=problem, student=self.student)


class ProblemFormTests(TestCase):

    def valid(self, **extra):
        data = {
            'title': 'Bai 1', 'description': 'Mo ta',
            'input_description': '', 'output_description': '',
            'constraints': '', 'difficulty': 'easy',
            'time_limit': 1, 'memory_limit': 256,
        }
        data.update(extra)
        return data

    def test_valid_problem_form(self):
        self.assertTrue(ProblemForm(self.valid()).is_valid())

    def test_title_required(self):
        self.assertFalse(ProblemForm(self.valid(title='')).is_valid())

    def test_test_case_form_requires_expected_output(self):
        self.assertFalse(TestCaseForm({'input_data': '1'}).is_valid())
        self.assertTrue(TestCaseForm(
            {'input_data': '1', 'expected_output': '1'}).is_valid())


class CreateAndLifecycleTests(ProblemTestBase):

    def test_teacher_creates_problem_as_draft(self):
        self.login(self.teacher)
        self.client.post(
            reverse('create_problem', args=[self.classroom.id]),
            problem_post('Bai moi'))
        problem = Problem.objects.get(title='Bai moi')
        self.assertEqual(problem.test_cases.count(), 1)
        self.assertEqual(problem.created_by, self.teacher)
        self.assertEqual(problem.status, 'draft')

    def test_publish_close_reopen(self):
        problem = make_problem(self.classroom, self.teacher, status='draft')
        self.login(self.teacher)
        self.client.post(reverse('publish_problem', args=[problem.id]))
        problem.refresh_from_db()
        self.assertEqual(problem.status, 'published')
        self.client.post(reverse('close_problem', args=[problem.id]))
        problem.refresh_from_db()
        self.assertEqual(problem.status, 'closed')
        self.client.post(reverse('reopen_problem', args=[problem.id]))
        problem.refresh_from_db()
        self.assertNotEqual(problem.status, 'closed')

    def test_other_teacher_cannot_publish(self):
        problem = make_problem(self.classroom, self.teacher, status='draft')
        self.login(self.other_teacher)
        self.client.post(reverse('publish_problem', args=[problem.id]))
        problem.refresh_from_db()
        self.assertEqual(problem.status, 'draft')

    def test_student_cannot_publish(self):
        problem = make_problem(self.classroom, self.teacher, status='draft')
        self.login(self.student)
        self.client.post(reverse('publish_problem', args=[problem.id]))
        problem.refresh_from_db()
        self.assertEqual(problem.status, 'draft')


class TestCaseViewTests(ProblemTestBase):

    def setUp(self):
        super().setUp()
        self.problem = make_problem(self.classroom, self.teacher)

    def test_teacher_adds_test_case(self):
        self.login(self.teacher)
        self.client.post(
            reverse('test_case_create', args=[self.problem.id]),
            {'input_data': '1 2', 'expected_output': '3'})
        self.assertEqual(self.problem.test_cases.count(), 1)

    def test_teacher_edits_and_deletes_test_case(self):
        add_tests(self.problem, [('1 2', '3')])
        case = self.problem.test_cases.get()
        self.login(self.teacher)
        self.client.post(
            reverse('test_case_edit', args=[self.problem.id, case.id]),
            {'input_data': '5 5', 'expected_output': '10'})
        case.refresh_from_db()
        self.assertEqual(case.expected_output, '10')
        self.client.post(
            reverse('test_case_delete', args=[self.problem.id, case.id]))
        self.assertEqual(Case.objects.count(), 0)

    def test_student_cannot_manage_test_cases(self):
        self.login(self.student)
        response = self.client.post(
            reverse('test_case_create', args=[self.problem.id]),
            {'input_data': '1', 'expected_output': '1'})
        self.assertEqual(Case.objects.count(), 0)
        self.assertEqual(response.status_code, 302)

    def test_list_page_for_teacher(self):
        self.login(self.teacher)
        self.assertEqual(self.client.get(
            reverse('test_case_list', args=[self.problem.id])
        ).status_code, 200)


class ProblemViewTests(ProblemTestBase):

    def test_list_and_detail_for_student(self):
        problem = make_problem(self.classroom, self.teacher)
        self.login(self.student)
        self.assertEqual(
            self.client.get(reverse('problem_list')).status_code, 200)
        self.assertEqual(self.client.get(
            reverse('problem_detail', args=[problem.id])).status_code, 200)

    def test_detail_for_teacher(self):
        problem = make_problem(self.classroom, self.teacher)
        self.login(self.teacher)
        self.assertEqual(self.client.get(
            reverse('problem_detail', args=[problem.id])).status_code, 200)

    def test_edit_problem_by_owner(self):
        problem = make_problem(self.classroom, self.teacher)
        self.login(self.teacher)
        self.client.post(
            reverse('edit_problem', args=[problem.id]),
            problem_post('Doi ten', cases=()))
        problem.refresh_from_db()
        self.assertEqual(problem.title, 'Doi ten')

    def test_export_problem_package(self):
        problem = make_problem(self.classroom, self.teacher)
        add_tests(problem)
        self.login(self.teacher)
        response = self.client.get(
            reverse('export_problem_package', args=[problem.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content)
