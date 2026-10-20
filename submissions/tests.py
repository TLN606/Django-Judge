import shutil
import unittest

from django.test import TestCase
from django.urls import reverse

from config.testing import (
    AC_CPP, PASSWORD, add_tests, join, make_classroom, make_problem, make_user,
)
from problems.models import ProblemAttempt
from submissions.grading import grade_submission
from submissions.models import Submission, SubmissionResult

HAS_GPP = shutil.which('g++') is not None
PY_SUM = 'a, b = map(int, input().split())\nprint(a + b)\n'


class SubmissionTestBase(TestCase):

    def setUp(self):
        self.teacher = make_user('gv01', role='teacher')
        self.student = make_user('sv01')
        self.outsider = make_user('sv02')
        self.classroom = make_classroom(self.teacher)
        join(self.classroom, self.student)
        self.problem = make_problem(self.classroom, self.teacher)
        add_tests(self.problem)

    def login(self, user):
        self.assertTrue(
            self.client.login(username=user.username, password=PASSWORD))

    def submit(self, code, language='python'):
        return self.client.post(
            reverse('submit_solution', args=[self.problem.id]),
            {'language': language, 'source_code': code})


class GradeSubmissionTests(SubmissionTestBase):

    def make_submission(self, code, language='python'):
        return Submission.objects.create(
            problem=self.problem, user=self.student,
            language=language, source_code=code, status='running')

    def test_all_tests_pass_gives_accepted_100(self):
        sub = grade_submission(self.make_submission(PY_SUM), self.problem)
        self.assertEqual(sub.status, 'accepted')
        self.assertEqual(sub.score, 100)
        self.assertEqual(SubmissionResult.objects.count(), 2)
        self.assertIsNotNone(sub.judged_at)

    def test_partial_pass_gives_proportional_score(self):
        code = (
            'a, b = map(int, input().split())\n'
            'print(a + b if a < 5 else 0)\n'
        )
        sub = grade_submission(self.make_submission(code), self.problem)
        self.assertEqual(sub.status, 'wrong_answer')
        self.assertEqual(sub.score, 50)

    def test_syntax_error_gives_compile_error(self):
        sub = grade_submission(
            self.make_submission('def f(:\n'), self.problem)
        self.assertEqual(sub.status, 'compile_error')
        self.assertEqual(sub.score, 0)

    def test_problem_without_tests_is_system_error(self):
        empty = make_problem(self.classroom, self.teacher, title='Rong')
        sub = Submission.objects.create(
            problem=empty, user=self.student, language='python',
            source_code=PY_SUM, status='running')
        grade_submission(sub, empty)
        self.assertEqual(sub.status, 'system_error')
        self.assertIn('no test cases', sub.error_message)

    @unittest.skipUnless(HAS_GPP, 'g++ is not installed')
    def test_cpp_solution_accepted(self):
        sub = grade_submission(
            self.make_submission(AC_CPP, 'cpp'), self.problem)
        self.assertEqual(sub.status, 'accepted')


class SubmitViewTests(SubmissionTestBase):

    def test_student_submit_creates_graded_submission(self):
        self.login(self.student)
        response = self.submit(PY_SUM)
        sub = Submission.objects.get()
        self.assertRedirects(
            response, reverse('submission_detail', args=[sub.id]))
        self.assertEqual(sub.status, 'accepted')
        attempt = ProblemAttempt.objects.get()
        self.assertEqual(attempt.status, 'locked')
        self.assertEqual(attempt.attempt_count, 1)

    def test_second_submit_is_blocked_until_reset(self):
        self.login(self.student)
        self.submit(PY_SUM)
        self.submit(PY_SUM)
        self.assertEqual(Submission.objects.count(), 1)

    def test_teacher_reset_allows_another_submit(self):
        self.login(self.student)
        self.submit(PY_SUM)
        self.client.logout()

        self.login(self.teacher)
        self.client.post(reverse(
            'reset_attempt', args=[self.problem.id, self.student.id]))
        attempt = ProblemAttempt.objects.get()
        self.assertEqual(attempt.status, 'available')
        self.assertEqual(attempt.reset_count, 1)
        self.assertEqual(attempt.last_reset_by, self.teacher)
        self.client.logout()

        self.login(self.student)
        self.submit(PY_SUM)
        self.assertEqual(Submission.objects.count(), 2)

    def test_student_cannot_reset_attempt(self):
        self.login(self.student)
        self.submit(PY_SUM)
        self.client.post(reverse(
            'reset_attempt', args=[self.problem.id, self.student.id]))
        self.assertEqual(ProblemAttempt.objects.get().status, 'locked')

    def test_non_member_cannot_submit(self):
        self.login(self.outsider)
        self.submit(PY_SUM)
        self.assertEqual(Submission.objects.count(), 0)

    def test_teacher_cannot_submit(self):
        self.login(self.teacher)
        self.submit(PY_SUM)
        self.assertEqual(Submission.objects.count(), 0)

    def test_draft_problem_rejects_submission(self):
        self.problem.status = 'draft'
        self.problem.save()
        self.login(self.student)
        self.submit(PY_SUM)
        self.assertEqual(Submission.objects.count(), 0)

    def test_get_shows_form(self):
        self.login(self.student)
        response = self.client.get(
            reverse('submit_solution', args=[self.problem.id]))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(
            reverse('submit_solution', args=[self.problem.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)


class SubmissionViewTests(SubmissionTestBase):

    def setUp(self):
        super().setUp()
        self.login(self.student)
        self.submit(PY_SUM)
        self.sub = Submission.objects.get()

    def test_owner_sees_detail(self):
        response = self.client.get(
            reverse('submission_detail', args=[self.sub.id]))
        self.assertEqual(response.status_code, 200)

    def test_other_student_cannot_see_detail(self):
        self.client.logout()
        self.login(self.outsider)
        response = self.client.get(
            reverse('submission_detail', args=[self.sub.id]))
        self.assertNotEqual(response.status_code, 200)

    def test_teacher_sees_submission_list(self):
        self.client.logout()
        self.login(self.teacher)
        response = self.client.get(
            reverse('submission_list', args=[self.problem.id]))
        self.assertEqual(response.status_code, 200)

    def test_student_sees_own_list(self):
        response = self.client.get(
            reverse('submission_list', args=[self.problem.id]))
        self.assertEqual(response.status_code, 200)

    def test_str(self):
        self.assertTrue(str(self.sub))
        self.assertTrue(str(self.sub.results.first()))
