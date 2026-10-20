from django.conf import settings
from django.db import models


from problems.models import Problem, ProblemAttempt


class Submission(models.Model):

    LANGUAGE_CHOICES = (
        ('cpp', 'C++'),
        ('python', 'Python'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('accepted', 'Accepted'),
        ('wrong_answer', 'Wrong Answer'),
        ('compile_error', 'Compile Error'),
        ('runtime_error', 'Runtime Error'),
        ('time_limit', 'Time Limit Exceeded'),
        ('memory_limit', 'Memory Limit Exceeded'),
        ('system_error', 'System Error'),
    )

    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name='submissions'
    )

    attempt = models.ForeignKey(
        ProblemAttempt,
        on_delete=models.CASCADE,
        related_name='submissions',
        null=True,
        blank=True
    )   

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submissions'
    )

    language = models.CharField(
        max_length=20,
        choices=LANGUAGE_CHOICES
    )

    source_code = models.TextField()

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='pending'
    )

    score = models.FloatField(
        default=0
    )

    execution_time = models.FloatField(
        null=True,
        blank=True,
        help_text='Execution time in seconds.'
    )

    memory_used = models.IntegerField(
        null=True,
        blank=True,
        help_text='Memory used in MB.'
    )

    error_message = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    judged_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return (
            f'{self.user.username} - '
            f'{self.problem.title} - '
            f'#{self.id}'
        )


class SubmissionResult(models.Model):

    STATUS_CHOICES = (
        ('accepted', 'Accepted'),
        ('wrong_answer', 'Wrong Answer'),
        ('compile_error', 'Compile Error'),
        ('runtime_error', 'Runtime Error'),
        ('time_limit', 'Time Limit Exceeded'),
        ('memory_limit', 'Memory Limit Exceeded'),
        ('system_error', 'System Error'),
    )

    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name='results'
    )

    test_case = models.ForeignKey(
        'problems.TestCase',
        on_delete=models.CASCADE,
        related_name='submission_results'
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES
    )

    execution_time = models.FloatField(
        null=True,
        blank=True,
        help_text='Execution time in seconds.'
    )

    memory_used = models.IntegerField(
        null=True,
        blank=True,
        help_text='Memory used in MB.'
    )

    actual_output = models.TextField(
        blank=True
    )

    error_message = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['test_case__id']

    def __str__(self):
        return (
            f'Submission #{self.submission.id} - '
            f'Test Case #{self.test_case.id}'
        )