from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from classrooms.models import ClassroomMember
from problems.models import Problem, ProblemAttempt
from .grading import grade_submission

from .forms import SubmissionForm
from .models import Submission


User = get_user_model()


@login_required
def submit_solution(request, problem_id):

    problem = get_object_or_404(
        Problem.objects.select_related(
            'classroom',
            'created_by'
        ),
        id=problem_id
    )

    classroom = problem.classroom

    # Teacher không nộp bài: chỉ xem bài tập của lớp mình
    if request.user.role == 'teacher':

        if classroom.teacher != request.user:
            return redirect('problem_list')

        return redirect(
            'problem_detail',
            problem_id=problem.id
        )

    # Student phải là thành viên lớp
    is_member = ClassroomMember.objects.filter(
        classroom=classroom,
        student=request.user
    ).exists()

    if not is_member:
        return redirect('problem_list')

    # Chỉ nhận bài khi bài tập đã published
    if problem.status != 'published':
        return redirect(
            'problem_detail',
            problem_id=problem.id
        )

    if request.method == 'POST':

        form = SubmissionForm(request.POST)

        if form.is_valid():

            submission = None

            # Khóa lượt làm bài trong transaction để tránh nộp trùng
            with transaction.atomic():

                attempt, created = (
                    ProblemAttempt.objects
                    .select_for_update()
                    .get_or_create(
                        problem=problem,
                        student=request.user,
                        defaults={'status': 'available'}
                    )
                )

                if not attempt.can_submit:

                    form.add_error(
                        None,
                        (
                            'You have already submitted '
                            'this problem. Please wait '
                            'for your teacher to reset '
                            'your attempt.'
                        )
                    )

                else:

                    submission = form.save(commit=False)
                    submission.problem = problem
                    submission.user = request.user
                    submission.attempt = attempt
                    submission.status = 'running'
                    submission.save()

                    attempt.status = 'locked'
                    attempt.attempt_count += 1
                    attempt.save()

            if submission is not None:

                grade_submission(submission, problem)

                return redirect(
                    'submission_detail',
                    submission_id=submission.id
                )

    else:

        form = SubmissionForm()

    return render(
        request,
        'submissions/submit.html',
        {
            'problem': problem,
            'form': form,
        }
    )


@login_required
def submission_detail(request, submission_id):

    submission = get_object_or_404(
        Submission.objects.select_related(
            'problem',
            'problem__classroom',
            'user',
        ).prefetch_related(
            'results__test_case'
        ),
        id=submission_id
    )

    # ==========================================
    # ACCESS CONTROL
    # ==========================================

    if request.user.role == 'student':

        # Student chỉ được xem submission của chính mình
        if submission.user != request.user:
            return redirect('problem_list')

    elif request.user.role == 'teacher':

        # Teacher chỉ xem submission
        # thuộc classroom mình phụ trách
        if submission.problem.classroom.teacher != request.user:
            return redirect('problem_list')

    # ==========================================
    # TEST CASE RESULTS
    # ==========================================

    test_results = submission.results.all()

    total_tests = test_results.count()

    passed_tests = test_results.filter(
        status='accepted'
    ).count()

    # ==========================================
    # RENDER
    # ==========================================

    return render(
        request,
        'submissions/detail.html',
        {
            'submission': submission,
            'test_results': test_results,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'is_teacher': request.user.role == 'teacher',
        }
    )

    submission = get_object_or_404(
        Submission.objects.select_related(
            'problem',
            'problem__classroom',
            'problem__classroom__teacher',
            'user',
        ),
        id=submission_id
    )

    # ==================================================
    # STUDENT ACCESS
    # ==================================================

    # Student chỉ xem submission của chính mình
    if request.user.role == 'student':

        if submission.user != request.user:

            return redirect(
                'problem_list'
            )

    # ==================================================
    # TEACHER ACCESS
    # ==================================================

    elif request.user.role == 'teacher':

        if (
            submission.problem.classroom.teacher
            != request.user
        ):

            return redirect(
                'problem_list'
            )

    # ==================================================
    # ADMIN
    # ==================================================

    # Superuser được phép xem submission

    # ==================================================
    # RENDER
    # ==================================================

    return render(
        request,
        'submissions/detail.html',
        {
            'submission': submission,
        }
    )


@login_required
def submission_list(request, problem_id):

    problem = get_object_or_404(
        Problem.objects.select_related(
            'classroom',
            'created_by'
        ),
        id=problem_id
    )

    # ==================================================
    # STUDENT
    # ==================================================

    if request.user.role == 'student':

        is_member = ClassroomMember.objects.filter(
            classroom=problem.classroom,
            student=request.user
        ).exists()

        if not is_member:
            return redirect('problem_list')

        submissions = (
            Submission.objects
            .filter(
                problem=problem,
                user=request.user
            )
            .select_related(
                'user',
                'problem',
                'attempt'
            )
            .order_by('-created_at')
        )

        return render(
            request,
            'submissions/list.html',
            {
                'problem': problem,
                'submissions': submissions,
                'is_teacher': False,
            }
        )

    # ==================================================
    # TEACHER
    # ==================================================

    if request.user.role == 'teacher':

        if problem.classroom.teacher != request.user:
            return redirect('problem_list')

        # ==============================================
        # GET STUDENTS IN CLASSROOM
        # ==============================================

        members = (
            ClassroomMember.objects
            .filter(
                classroom=problem.classroom
            )
            .select_related('student')
        )

        students = [
            member.student
            for member in members
        ]

        # ==============================================
        # GET / CREATE ATTEMPT FOR EVERY STUDENT
        # ==============================================

        student_attempts = []

        for student in students:

            attempt, created = (
                ProblemAttempt.objects.get_or_create(
                    problem=problem,
                    student=student,
                    defaults={
                        'status': 'available',
                    }
                )
            )

            latest_submission = (
                Submission.objects
                .filter(
                    problem=problem,
                    user=student,
                    attempt=attempt
                )
                .order_by('-created_at')
                .first()
            )

            student_attempts.append({
                'student': student,
                'attempt': attempt,
                'submission': latest_submission,
            })

        # ==============================================
        # ALL SUBMISSIONS FOR THIS PROBLEM
        # ==============================================

        submissions = (
            Submission.objects
            .filter(
                problem=problem
            )
            .select_related(
                'user',
                'problem',
                'attempt'
            )
            .order_by('-created_at')
        )

        return render(
            request,
            'submissions/list.html',
            {
                'problem': problem,
                'student_attempts': student_attempts,
                'submissions': submissions,
                'is_teacher': True,
            }
        )

    # ==================================================
    # FALLBACK
    # ==================================================

    return redirect('problem_list')


@login_required
def reset_attempt(
    request,
    problem_id,
    student_id
):

    # ==================================================
    # ONLY HANDLE POST
    # ==================================================

    if request.method != 'POST':
        return redirect(
            'problem_detail',
            problem_id=problem_id
        )

    # ==================================================
    # GET PROBLEM
    # ==================================================

    problem = get_object_or_404(
        Problem.objects.select_related(
            'classroom'
        ),
        id=problem_id
    )

    # ==================================================
    # AUTHORIZATION
    # ==================================================

    is_admin = request.user.is_superuser

    is_teacher = (
        request.user.role == 'teacher'
        and problem.classroom.teacher == request.user
    )

    if not is_admin and not is_teacher:

        return redirect(
            'problem_detail',
            problem_id=problem.id
        )

    # ==================================================
    # GET STUDENT
    # ==================================================

    student = get_object_or_404(
        User,
        id=student_id
    )

    # ==================================================
    # GET ATTEMPT
    # ==================================================

    attempt = get_object_or_404(
        ProblemAttempt,
        problem=problem,
        student=student
    )

    # ==================================================
    # RESET
    # ==================================================

    attempt.status = 'available'

    attempt.reset_count += 1

    attempt.last_reset_by = request.user

    attempt.last_reset_at = timezone.now()

    attempt.save()

    # ==================================================
    # RETURN
    # ==================================================

    return redirect(
        'submission_list',
        problem_id=problem.id
    )