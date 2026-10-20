from django.test import TestCase
from django.urls import reverse

from accounts.forms import RegisterForm
from accounts.models import User
from config.testing import PASSWORD, make_user


class RegisterFormTests(TestCase):

    def data(self, **extra):
        base = {
            'username': 'sv01',
            'email': 'sv01@example.com',
            'password1': PASSWORD,
            'password2': PASSWORD,
        }
        base.update(extra)
        return base

    def test_valid_form_creates_student(self):
        form = RegisterForm(self.data())
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.role, 'student')
        self.assertEqual(user.email, 'sv01@example.com')

    def test_email_is_required(self):
        self.assertFalse(RegisterForm(self.data(email='')).is_valid())

    def test_password_mismatch_is_rejected(self):
        self.assertFalse(
            RegisterForm(self.data(password2='khac-hoan-toan-1')).is_valid()
        )


class AuthViewTests(TestCase):

    def test_register_logs_in_and_redirects(self):
        response = self.client.post(reverse('register'), {
            'username': 'sv02',
            'email': 'sv02@example.com',
            'password1': PASSWORD,
            'password2': PASSWORD,
        })
        self.assertRedirects(response, reverse('classroom_list'))
        self.assertTrue(User.objects.filter(username='sv02').exists())

    def test_register_cannot_choose_teacher_role(self):
        self.client.post(reverse('register'), {
            'username': 'hacker',
            'email': 'h@example.com',
            'password1': PASSWORD,
            'password2': PASSWORD,
            'role': 'teacher',
        })
        self.assertEqual(User.objects.get(username='hacker').role, 'student')

    def test_register_page_renders_for_anonymous(self):
        self.assertEqual(self.client.get(reverse('register')).status_code, 200)

    def test_authenticated_user_is_redirected_from_register(self):
        make_user('sv03')
        self.client.login(username='sv03', password=PASSWORD)
        response = self.client.get(reverse('register'))
        self.assertRedirects(response, reverse('home'),
                             fetch_redirect_response=False)

    def test_login_with_valid_credentials(self):
        make_user('sv04')
        response = self.client.post(reverse('login'), {
            'username': 'sv04', 'password': PASSWORD,
        })
        self.assertEqual(response.status_code, 302)

    def test_login_with_wrong_password_shows_form_again(self):
        make_user('sv05')
        response = self.client.post(reverse('login'), {
            'username': 'sv05', 'password': 'sai-mat-khau',
        })
        self.assertEqual(response.status_code, 200)

    def test_protected_page_redirects_to_login(self):
        response = self.client.get(reverse('classroom_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)


class UserModelTests(TestCase):

    def test_str_contains_username(self):
        self.assertIn('gv01', str(make_user('gv01', role='teacher')))


class SeedDemoCommandTests(TestCase):

    def test_seed_is_idempotent(self):
        from django.core.management import call_command
        from classrooms.models import Classroom
        from problems.models import Problem

        call_command('seed_demo', verbosity=0)
        call_command('seed_demo', verbosity=0)
        self.assertEqual(User.objects.count(), 3)
        self.assertEqual(Classroom.objects.count(), 1)
        self.assertEqual(Problem.objects.count(), 2)
        self.assertTrue(
            User.objects.get(username='teacher_demo').check_password(
                'Demo@12345'))
