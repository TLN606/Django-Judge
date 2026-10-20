from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'role',
        'is_active',
    )

    list_filter = (
        'role',
        'is_active',
    )

    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
    )

    fieldsets = (
        (
            'Account',
            {
                'fields': (
                    'username',
                    'password',
                )
            }
        ),

        (
            'Personal Information',
            {
                'fields': (
                    'first_name',
                    'last_name',
                    'email',
                )
            }
        ),

        (
            'MiniJudge Information',
            {
                'fields': (
                    'role',
                )
            }
        ),

        (
            'Status',
            {
                'fields': (
                    'is_active',
                )
            }
        ),
    )

    add_fieldsets = (
        (
            'Account',
            {
                'classes': ('wide',),
                'fields': (
                    'username',
                    'password1',
                    'password2',
                ),
            },
        ),

        (
            'Personal Information',
            {
                'fields': (
                    'first_name',
                    'last_name',
                    'email',
                )
            }
        ),

        (
            'MiniJudge Information',
            {
                'fields': (
                    'role',
                )
            }
        ),

        (
            'Status',
            {
                'fields': (
                    'is_active',
                )
            }
        ),
    )