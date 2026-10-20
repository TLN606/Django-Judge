"""Hàm dựng dữ liệu dùng chung cho các test."""
from accounts.models import User
from classrooms.models import Classroom, ClassroomMember
from problems.models import Problem, TestCase

PASSWORD = 'Test@12345'

AC_CPP = (
    '#include <iostream>\n'
    'int main(){long long a,b;std::cin>>a>>b;std::cout<<a+b;}\n'
)


def make_user(username, role='student', **extra):
    return User.objects.create_user(
        username=username,
        password=PASSWORD,
        role=role,
        **extra,
    )


def make_classroom(teacher, code='LOP0001', name='Lop thu nghiem'):
    return Classroom.objects.create(
        name=name,
        code=code,
        teacher=teacher,
    )


def join(classroom, student):
    return ClassroomMember.objects.create(
        classroom=classroom,
        student=student,
    )


def make_problem(classroom, teacher, status='published', **extra):
    problem = Problem.objects.create(
        classroom=classroom,
        title=extra.pop('title', 'Tong hai so'),
        description='Cho a, b. In a + b.',
        status=status,
        created_by=teacher,
        **extra,
    )
    return problem


def add_tests(problem, pairs=(('1 2', '3'), ('10 20', '30'))):
    for index, (data, expected) in enumerate(pairs):
        TestCase.objects.create(
            problem=problem,
            input_data=data,
            expected_output=expected,
            is_sample=(index == 0),
        )
