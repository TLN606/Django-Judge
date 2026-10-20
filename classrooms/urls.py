from django.urls import path

from .views import create_classroom

from .views import (
    classroom_detail,
    classroom_list,
    join_classroom,
)

from .views import (
    kick_member,
    ban_member,
    unban_member,
)

urlpatterns = [

    path(
        '',
        classroom_list,
        name='classroom_list'
    ),

    path(
        '<int:classroom_id>/',
        classroom_detail,
        name='classroom_detail'
    ),
    
    path(
    'join/',
    join_classroom,
    name='join_classroom'
    ),

    path(
    'create/',
    create_classroom,
    name='create_classroom'
    ),

    path(
    '<int:classroom_id>/members/<int:student_id>/kick/',
    kick_member,
    name='kick_member'
    ),

    path(
        '<int:classroom_id>/members/<int:student_id>/ban/',
        ban_member,
        name='ban_member'
    ),

    path(
        '<int:classroom_id>/members/<int:student_id>/unban/',
        unban_member,
        name='unban_member'
),

]