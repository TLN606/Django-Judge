from django.urls import path

from .views import (
    submit_solution,
    submission_detail,
    submission_list,
    reset_attempt,
)


urlpatterns = [

    path(
        'problem/<int:problem_id>/submit/',
        submit_solution,
        name='submit_solution'
    ),

    path(
        'problem/<int:problem_id>/',
        submission_list,
        name='submission_list'
    ),

    path(
        '<int:submission_id>/',
        submission_detail,
        name='submission_detail'
    ),

    path(
        'problem/<int:problem_id>/reset/<int:student_id>/',
        reset_attempt,
        name='reset_attempt'
    ),

]