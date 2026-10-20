from django.contrib import admin

from .models import Classroom, ClassroomMember


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'code',
        'teacher',
        'created_at',
    )

    search_fields = (
        'name',
        'code',
        'teacher__username',
    )


@admin.register(ClassroomMember)
class ClassroomMemberAdmin(admin.ModelAdmin):

    list_display = (
        'classroom',
        'student',
        'joined_at',
    )

    search_fields = (
        'classroom__name',
        'student__username',
    )