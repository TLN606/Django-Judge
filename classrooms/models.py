from django.conf import settings
from django.db import models


class Classroom(models.Model):

    name = models.CharField(
        max_length=200
    )

    code = models.CharField(
        max_length=20,
        unique=True
    )

    description = models.TextField(
        blank=True
    )

    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teaching_classes'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name


class ClassroomMember(models.Model):

    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name='members'
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='joined_classes'
    )

    joined_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['classroom', 'student'],
                name='unique_classroom_student'
            )
        ]

    def __str__(self):
        return f'{self.student.username} - {self.classroom.name}'

class ClassroomBan(models.Model):
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name='bans'
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='classroom_bans'
    )

    banned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='issued_classroom_bans'
    )

    reason = models.TextField(blank=True)

    banned_at = models.DateTimeField(auto_now_add=True)
    unbanned_at = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['classroom', 'student'],
                name='unique_classroom_ban'
            )
        ]
        ordering = ['-banned_at']

    def __str__(self):
        return f'{self.student.username} - {self.classroom.name}'