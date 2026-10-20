from django.contrib import admin

from .models import Problem, TestCase
from .models import ProblemAttempt



@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'classroom',
        'difficulty',
        'created_by',
        'created_at',
    )

    list_filter = (
        'difficulty',
        'classroom',
    )

    search_fields = (
        'title',
        'description',
        'classroom__name',
        'created_by__username',
    )

    ordering = (
        '-created_at',
    )


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):

    list_display = (
        'problem',
        'id',
        'is_sample',
        'created_at',
    )

    list_filter = (
        'is_sample',
        'problem__classroom',
    )

    search_fields = (
        'problem__title',
        'input_data',
        'expected_output',
    )

    ordering = (
        'problem',
        'id',
    )


@admin.register(ProblemAttempt)
class ProblemAttemptAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'student',
        'problem',
        'status',
        'attempt_count',
        'reset_count',
        'last_reset_by',
        'last_reset_at',
        'updated_at',
    )

    list_filter = (
        'status',
        'reset_count',
        'updated_at',
    )

    search_fields = (
        'student__username',
        'problem__title',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'last_reset_at',
    )

    ordering = (
        '-updated_at',
    )