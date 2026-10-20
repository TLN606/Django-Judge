from django.urls import path

from .views import (
    problem_list,
    problem_detail,

    create_problem,
    import_problem_package,
    export_problem_package,

    test_case_list,
    test_case_create,
    test_case_edit,
    test_case_delete,

    publish_problem,
    close_problem,
    reopen_problem,
    edit_problem,
)


urlpatterns = [

    # =====================================================
    # PROBLEMS
    # =====================================================

    path(
        '',
        problem_list,
        name='problem_list'
    ),

    path(
        '<int:problem_id>/',
        problem_detail,
        name='problem_detail'
    ),

    path(
        '<int:problem_id>/edit/',
        edit_problem,
        name='edit_problem'
    ),


    # =====================================================
    # CREATE / IMPORT
    # =====================================================

    path(
        'classroom/<int:classroom_id>/create/',
        create_problem,
        name='create_problem'
    ),

    path(
        'classroom/<int:classroom_id>/import/',
        import_problem_package,
        name='import_problem_package'
    ),


    # =====================================================
    # TEST CASES
    # =====================================================

    path(
        '<int:problem_id>/test-cases/',
        test_case_list,
        name='test_case_list'
    ),

    path(
        '<int:problem_id>/test-cases/add/',
        test_case_create,
        name='test_case_create'
    ),

    path(
        '<int:problem_id>/test-cases/<int:test_case_id>/edit/',
        test_case_edit,
        name='test_case_edit'
    ),

    path(
        '<int:problem_id>/test-cases/<int:test_case_id>/delete/',
        test_case_delete,
        name='test_case_delete'
    ),


    # =====================================================
    # PROBLEM LIFECYCLE
    # =====================================================

    path(
        '<int:problem_id>/publish/',
        publish_problem,
        name='publish_problem'
    ),

    path(
        '<int:problem_id>/close/',
        close_problem,
        name='close_problem'
    ),

    path(
        '<int:problem_id>/reopen/',
        reopen_problem,
        name='reopen_problem'
    ),

    path(
        '<int:problem_id>/export/',
        export_problem_package,
        name='export_problem_package'
    ),

    

]