from django.test import TestCase
from django.urls import reverse

from classrooms.models import Classroom, ClassroomBan, ClassroomMember
from config.testing import PASSWORD, join, make_classroom, make_user


class ClassroomTestBase(TestCase):

    def setUp(self):
        self.teacher = make_user('gv01', role='teacher')
        self.other_teacher = make_user('gv02', role='teacher')
        self.student = make_user('sv01')
        self.classroom = make_classroom(self.teacher)

    def login(self, user):
        self.assertTrue(
            self.client.login(username=user.username, password=PASSWORD)
        )


class CreateClassroomTests(ClassroomTestBase):

    def test_teacher_can_create_classroom(self):
        self.login(self.teacher)
        response = self.client.post(reverse('create_classroom'), {
            'name': 'Cong nghe phan mem',
            'description': 'Lop moi',
        })
        created = Classroom.objects.get(name='Cong nghe phan mem')
        self.assertEqual(created.teacher, self.teacher)
        self.assertTrue(created.code.startswith('GV01'))
        self.assertRedirects(
            response,
            reverse('classroom_detail', args=[created.id]),
        )

    def test_student_cannot_create_classroom(self):
        self.login(self.student)
        self.client.post(reverse('create_classroom'), {'name': 'X'})
        self.assertFalse(Classroom.objects.filter(name='X').exists())


class JoinClassroomTests(ClassroomTestBase):

    def post_code(self, code):
        return self.client.post(reverse('join_classroom'), {'code': code})

    def test_student_joins_with_valid_code(self):
        self.login(self.student)
        self.post_code(self.classroom.code)
        self.assertTrue(ClassroomMember.objects.filter(
            classroom=self.classroom, student=self.student).exists())

    def test_code_is_case_insensitive(self):
        self.login(self.student)
        self.post_code(self.classroom.code.lower())
        self.assertEqual(self.classroom.members.count(), 1)

    def test_unknown_code_does_not_join(self):
        self.login(self.student)
        response = self.post_code('KHONGCO')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ClassroomMember.objects.count(), 0)

    def test_banned_student_cannot_join(self):
        ClassroomBan.objects.create(
            classroom=self.classroom, student=self.student,
            banned_by=self.teacher, is_active=True)
        self.login(self.student)
        self.post_code(self.classroom.code)
        self.assertEqual(ClassroomMember.objects.count(), 0)

    def test_joining_twice_keeps_one_membership(self):
        self.login(self.student)
        self.post_code(self.classroom.code)
        self.post_code(self.classroom.code)
        self.assertEqual(ClassroomMember.objects.count(), 1)

    def test_teacher_cannot_join_as_student(self):
        self.login(self.other_teacher)
        self.post_code(self.classroom.code)
        self.assertEqual(ClassroomMember.objects.count(), 0)

    def test_form_page_renders(self):
        self.login(self.student)
        self.assertEqual(
            self.client.get(reverse('join_classroom')).status_code, 200)


class MemberManagementTests(ClassroomTestBase):

    def setUp(self):
        super().setUp()
        join(self.classroom, self.student)

    def url(self, name):
        return reverse(name, args=[self.classroom.id, self.student.id])

    def test_owner_can_kick_member(self):
        self.login(self.teacher)
        self.client.post(self.url('kick_member'))
        self.assertEqual(ClassroomMember.objects.count(), 0)

    def test_other_teacher_cannot_kick_member(self):
        self.login(self.other_teacher)
        self.client.post(self.url('kick_member'))
        self.assertEqual(ClassroomMember.objects.count(), 1)

    def test_student_cannot_kick_member(self):
        self.login(self.student)
        self.client.post(self.url('kick_member'))
        self.assertEqual(ClassroomMember.objects.count(), 1)

    def test_kick_requires_post(self):
        self.login(self.teacher)
        response = self.client.get(self.url('kick_member'))
        self.assertEqual(response.status_code, 405)

    def test_ban_then_unban(self):
        self.login(self.teacher)
        self.client.post(self.url('ban_member'), {'reason': 'spam'})
        ban = ClassroomBan.objects.get(student=self.student)
        self.assertTrue(ban.is_active)
        self.assertEqual(ClassroomMember.objects.count(), 0)

        self.client.post(self.url('unban_member'))
        ban.refresh_from_db()
        self.assertFalse(ban.is_active)


class ClassroomViewTests(ClassroomTestBase):

    def test_list_and_detail_render_for_owner(self):
        self.login(self.teacher)
        self.assertEqual(
            self.client.get(reverse('classroom_list')).status_code, 200)
        self.assertEqual(self.client.get(
            reverse('classroom_detail', args=[self.classroom.id])
        ).status_code, 200)

    def test_member_sees_detail(self):
        join(self.classroom, self.student)
        self.login(self.student)
        self.assertEqual(self.client.get(
            reverse('classroom_detail', args=[self.classroom.id])
        ).status_code, 200)

    def test_missing_classroom_is_404(self):
        self.login(self.teacher)
        self.assertEqual(self.client.get(
            reverse('classroom_detail', args=[9999])).status_code, 404)

    def test_str(self):
        self.assertIn(self.classroom.name, str(self.classroom))
