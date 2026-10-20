from django.conf import settings
from django.db import models

from classrooms.models import Classroom


class Problem(models.Model):

    DIFFICULTY_CHOICES = (
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    )

    STATUS_CHOICES = (
    ('draft', 'Draft'),
    ('published', 'Published'),
    ('closed', 'Closed'),
    )

    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name='problems'
    )

    title = models.CharField(
        max_length=200
    )

    description = models.TextField()

    input_description = models.TextField(
        blank=True
    )

    output_description = models.TextField(
        blank=True
    )

    constraints = models.TextField(
        blank=True
    )

    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='easy'
    )

    status = models.CharField(
    max_length=20,
    choices=STATUS_CHOICES,
        default='draft'
)

    time_limit = models.FloatField(
        default=1.0,
        help_text='Time limit in seconds.'
    )

    memory_limit = models.IntegerField(
        default=256,
        help_text='Memory limit in MB.'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_problems'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class TestCase(models.Model):

    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name='test_cases'
    )

    input_data = models.TextField(
        blank=True
    )

    expected_output = models.TextField()

    is_sample = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.problem.title} - Test Case {self.id}'

class ProblemAttempt(models.Model):

    STATUS_CHOICES = (
        ('available', 'Available'),
        ('locked', 'Locked'),
    )

    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name='attempts'
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='problem_attempts'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available'
    )

    attempt_count = models.PositiveIntegerField(
        default=0
    )

    reset_count = models.PositiveIntegerField(
        default=0
    )

    last_reset_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reset_problem_attempts'
    )

    last_reset_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=['problem', 'student'],
                name='unique_problem_student_attempt'
            )
        ]

        ordering = ['-updated_at']

    @property
    def can_submit(self):
        return self.status == 'available'

    def __str__(self):

        return (
            f'{self.student.username} - '
            f'{self.problem.title}'
        )