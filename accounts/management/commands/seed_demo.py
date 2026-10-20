"""Tạo dữ liệu mẫu để demo: 1 giáo viên, 2 sinh viên, 1 lớp, 2 bài tập."""
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from classrooms.models import Classroom, ClassroomMember
from problems.models import Problem, TestCase

DEMO_PASSWORD = 'Demo@12345'

PROBLEMS = [
    {
        'title': 'Tong hai so',
        'description': 'Cho hai so nguyen a, b. In ra a + b.',
        'input_description': 'Mot dong gom hai so nguyen a, b.',
        'output_description': 'Mot so nguyen la tong a + b.',
        'constraints': '|a|, |b| <= 10^9',
        'difficulty': 'easy',
        'tests': [('1 2', '3'), ('10 20', '30'), ('-5 5', '0')],
    },
    {
        'title': 'Tong cac chu so',
        'description': 'Cho so nguyen duong n. In tong cac chu so cua n.',
        'input_description': 'Mot dong chua so nguyen duong n.',
        'output_description': 'Tong cac chu so cua n.',
        'constraints': '1 <= n <= 10^18',
        'difficulty': 'medium',
        'tests': [('123', '6'), ('9', '9'), ('1000000', '1')],
    },
]


class Command(BaseCommand):
    help = 'Tao du lieu mau (idempotent) de demo he thong.'

    @transaction.atomic
    def handle(self, *args, **options):
        teacher = self._user('teacher_demo', 'teacher')
        students = [
            self._user('student_demo', 'student'),
            self._user('student_demo2', 'student'),
        ]

        classroom, _ = Classroom.objects.get_or_create(
            code='DEMO0001',
            defaults={
                'name': 'Cong nghe phan mem - Demo',
                'description': 'Lop mau de demo.',
                'teacher': teacher,
            },
        )
        for student in students:
            ClassroomMember.objects.get_or_create(
                classroom=classroom, student=student)

        for item in PROBLEMS:
            problem, created = Problem.objects.get_or_create(
                classroom=classroom,
                title=item['title'],
                defaults={
                    'description': item['description'],
                    'input_description': item['input_description'],
                    'output_description': item['output_description'],
                    'constraints': item['constraints'],
                    'difficulty': item['difficulty'],
                    'status': 'published',
                    'created_by': teacher,
                },
            )
            if created:
                for index, (data, expected) in enumerate(item['tests']):
                    TestCase.objects.create(
                        problem=problem,
                        input_data=data,
                        expected_output=expected,
                        is_sample=(index == 0),
                    )

        self.stdout.write(self.style.SUCCESS(
            'Seed xong. Tai khoan demo (mat khau chung '
            f'{DEMO_PASSWORD}): teacher_demo, student_demo, '
            'student_demo2. Ma lop: DEMO0001.'))

    def _user(self, username, role):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'role': role, 'email': f'{username}@example.com'},
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
        return user
