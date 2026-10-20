import os
import zipfile

from django.core.files.uploadedfile import UploadedFile

from .services.package_importer import (
    ProblemPackageError,
    validate_package,
)

from django.http import HttpResponse

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from django.contrib import messages
from django.views.decorators.http import require_POST
from classrooms.models import ClassroomMember

from django.db import transaction

from .forms import TestCaseForm, TestCaseFormSet
from .forms import ProblemForm

from .models import Problem, TestCase, Classroom


def teacher_required(view_func):
    return user_passes_test(
        lambda user: user.is_authenticated and user.role == 'teacher'
    )(view_func)



@login_required
def problem_list(request):

    if request.user.role == 'teacher':

        problems = (
            Problem.objects
            .filter(
                classroom__teacher=request.user
            )
            .select_related(
                'classroom',
                'created_by'
            )
            .order_by('-created_at')
        )

    else:

        problems = (
            Problem.objects
            .filter(
                classroom__members__student=request.user,
                status__in=[
                    'published',
                    'closed',
                ]
            )
            .select_related(
                'classroom',
                'created_by'
            )
            .order_by('-created_at')
        )

    return render(
        request,
        'problems/list.html',
        {
            'problems': problems,
        }
    )



@login_required
def problem_detail(request, problem_id):

    problem = get_object_or_404(
        Problem.objects.select_related(
            'classroom',
            'created_by'
        ),
        id=problem_id
    )

    classroom = problem.classroom

    # ==================================================
    # TEACHER
    # ==================================================

    if request.user.role == 'teacher':

        # Teacher chỉ được xem problem
        # thuộc classroom mình dạy
        if classroom.teacher != request.user:
            return redirect('problem_list')


    # ==================================================
    # STUDENT
    # ==================================================

    else:

        # Student phải là thành viên classroom
        is_member = ClassroomMember.objects.filter(
            classroom=classroom,
            student=request.user
        ).exists()

        if not is_member:
            return redirect('problem_list')

        # Student không được xem DRAFT
        if problem.status == 'draft':
            return redirect('problem_list')


    # ==================================================
    # RENDER
    # ==================================================

    return render(
        request,
        'problems/detail.html',
        {
            'problem': problem,
        }
    )

    problem = get_object_or_404(
        Problem.objects.select_related(
            'classroom',
            'created_by'
        ),
        id=problem_id
    )

    classroom = problem.classroom

    # Teacher chỉ được xem problem
    # thuộc classroom mình dạy
    if request.user.role == 'teacher':

        if classroom.teacher != request.user:
            return redirect('problem_list')

    # Student phải là thành viên classroom
    else:

        is_member = ClassroomMember.objects.filter(
            classroom=classroom,
            student=request.user
        ).exists()

        if not is_member:
            return redirect('problem_list')

    return render(
        request,
        'problems/detail.html',
        {
            'problem': problem,
        }
    )


@teacher_required
def test_case_list(request, problem_id):

    problem = get_object_or_404(
        Problem.objects.select_related(
            'classroom',
            'created_by'
        ),
        id=problem_id
    )

    if problem.classroom.teacher != request.user:
        return redirect('problem_list')

    test_cases = problem.test_cases.all()

    return render(
        request,
        'problems/test_cases.html',
        {
            'problem': problem,
            'test_cases': test_cases,
        }
    )
    problem = get_object_or_404(
        Problem.objects.select_related(
            'classroom',
            'created_by'
        ),
        id=problem_id
    )

    test_cases = problem.test_cases.all()

    return render(
        request,
        'problems/test_cases.html',
        {
            'problem': problem,
            'test_cases': test_cases,
        }
    )

@teacher_required
def test_case_create(request, problem_id):

    problem = get_object_or_404(
        Problem.objects.select_related(
            'classroom',
            'created_by'
        ),
        id=problem_id
    )

    if problem.classroom.teacher != request.user:
        return redirect('problem_list')

    if request.method == 'POST':

        form = TestCaseForm(request.POST)

        if form.is_valid():

            test_case = form.save(commit=False)

            test_case.problem = problem

            test_case.save()

            return redirect(
                'test_case_list',
                problem_id=problem.id
            )

    else:

        form = TestCaseForm()

    return render(
        request,
        'problems/test_case_form.html',
        {
            'problem': problem,
            'form': form
        }
    )

    problem = get_object_or_404(
        Problem.objects.select_related(
            'classroom',
            'created_by'
        ),
        id=problem_id
    )

    if request.method == 'POST':

        form = TestCaseForm(request.POST)

        if form.is_valid():

            test_case = form.save(commit=False)
            test_case.problem = problem
            test_case.save()

            return redirect(
                'test_case_list',
                problem_id=problem.id
            )

    else:

        form = TestCaseForm()

    return render(
        request,
        'problems/test_case_form.html',
        {
            'problem': problem,
            'form': form,
        }
    )

@teacher_required
def test_case_edit(request, problem_id, test_case_id):

    problem = get_object_or_404(
        Problem.objects.select_related(
            'classroom',
            'created_by'
        ),
        id=problem_id
    )

    # Chỉ teacher sở hữu classroom mới được sửa
    if problem.classroom.teacher != request.user:
        return redirect('problem_list')

    test_case = get_object_or_404(
        TestCase,
        id=test_case_id,
        problem=problem
    )

    if request.method == 'POST':

        form = TestCaseForm(
            request.POST,
            instance=test_case
        )

        if form.is_valid():

            form.save()

            return redirect(
                'test_case_list',
                problem_id=problem.id
            )

    else:

        form = TestCaseForm(
            instance=test_case
        )

    return render(
        request,
        'problems/test_case_form.html',
        {
            'problem': problem,
            'form': form,
            'editing': True,
            'test_case': test_case,
        }
    )

    problem = get_object_or_404(
        Problem.objects.select_related(
            'classroom',
            'created_by'
        ),
        id=problem_id
    )

    test_case = get_object_or_404(
        TestCase,
        id=test_case_id,
        problem=problem
    )

    if request.method == 'POST':

        form = TestCaseForm(
            request.POST,
            instance=test_case
        )

        if form.is_valid():

            form.save()

            return redirect(
                'test_case_list',
                problem_id=problem.id
            )

    else:

        form = TestCaseForm(
            instance=test_case
        )

    return render(
        request,
        'problems/test_case_form.html',
        {
            'problem': problem,
            'form': form,
            'editing': True,
            'test_case': test_case,
        }
    )

@teacher_required
def test_case_delete(request, problem_id, test_case_id):

    problem = get_object_or_404(
        Problem.objects.select_related(
            'classroom',
            'created_by'
        ),
        id=problem_id
    )

    # Chỉ teacher sở hữu classroom mới được xóa
    if problem.classroom.teacher != request.user:
        return redirect('problem_list')

    test_case = get_object_or_404(
        TestCase,
        id=test_case_id,
        problem=problem
    )

    if request.method == 'POST':

        test_case.delete()

        return redirect(
            'test_case_list',
            problem_id=problem.id
        )

    return render(
        request,
        'problems/test_case_confirm_delete.html',
        {
            'problem': problem,
            'test_case': test_case,
        }
    )

    problem = get_object_or_404(
        Problem.objects.select_related(
            'classroom',
            'created_by'
        ),
        id=problem_id
    )

    test_case = get_object_or_404(
        TestCase,
        id=test_case_id,
        problem=problem
    )

    if request.method == 'POST':

        test_case.delete()

        return redirect(
            'test_case_list',
            problem_id=problem.id
        )

    return render(
        request,
        'problems/test_case_confirm_delete.html',
        {
            'problem': problem,
            'test_case': test_case,
        }
    )

@login_required
@require_POST
def publish_problem(request, problem_id):

    problem = get_object_or_404(
        Problem.objects.select_related('classroom'),
        id=problem_id
    )

    # Chỉ Teacher sở hữu Classroom hoặc Admin
    if not request.user.is_superuser and problem.classroom.teacher != request.user:
        return redirect(
            'problem_detail',
            problem_id=problem.id
        )

    problem.status = 'published'
    problem.save(update_fields=['status'])

    messages.success(
        request,
        f'"{problem.title}" has been published.'
    )

    return redirect(
        'problem_detail',
        problem_id=problem.id
    )


@login_required
@require_POST
def close_problem(request, problem_id):

    problem = get_object_or_404(
        Problem.objects.select_related('classroom'),
        id=problem_id
    )

    # Chỉ Teacher sở hữu Classroom hoặc Admin
    if not request.user.is_superuser and problem.classroom.teacher != request.user:
        return redirect(
            'problem_detail',
            problem_id=problem.id
        )

    problem.status = 'closed'
    problem.save(update_fields=['status'])

    messages.success(
        request,
        f'"{problem.title}" has been closed.'
    )

    return redirect(
        'problem_detail',
        problem_id=problem.id
    )


@login_required
@require_POST
def reopen_problem(request, problem_id):

    problem = get_object_or_404(
        Problem.objects.select_related('classroom'),
        id=problem_id
    )

    # Chỉ Teacher sở hữu Classroom hoặc Admin
    if not request.user.is_superuser and problem.classroom.teacher != request.user:
        return redirect(
            'problem_detail',
            problem_id=problem.id
        )

    problem.status = 'published'
    problem.save(update_fields=['status'])

    messages.success(
        request,
        f'"{problem.title}" has been reopened.'
    )

    return redirect(
        'problem_detail',
        problem_id=problem.id
    )

@login_required
def create_problem(request, classroom_id):

    classroom = get_object_or_404(
        Classroom,
        id=classroom_id
    )

    # Chỉ Teacher sở hữu classroom hoặc Admin
    if not request.user.is_superuser and classroom.teacher != request.user:
        return redirect(
            'classroom_detail',
            classroom_id=classroom.id
        )

    if request.method == 'POST':

        form = ProblemForm(request.POST)

        if form.is_valid():

            formset = TestCaseFormSet(
                request.POST
            )

            if formset.is_valid():

                with transaction.atomic():

                    # =========================
                    # CREATE PROBLEM
                    # =========================

                    problem = form.save(commit=False)

                    problem.classroom = classroom
                    problem.created_by = request.user
                    problem.status = 'draft'

                    problem.save()


                    # =========================
                    # CREATE TEST CASES
                    # =========================

                    formset.instance = problem
                    formset.save()


                messages.success(
                    request,
                    f'"{problem.title}" has been created successfully.'
                )

                return redirect(
                    'problem_detail',
                    problem_id=problem.id
                )

    else:

        form = ProblemForm()

        formset = TestCaseFormSet()


    return render(
        request,
        'problems/create.html',
        {
            'form': form,
            'formset': formset,
            'classroom': classroom,
        }
    )

    classroom = get_object_or_404(
        Classroom,
        id=classroom_id
    )

    # Chỉ Teacher sở hữu classroom hoặc Admin
    if not request.user.is_superuser and classroom.teacher != request.user:
        return redirect(
            'classroom_detail',
            classroom_id=classroom.id
        )

    if request.method == 'POST':

        form = ProblemForm(request.POST)

        if form.is_valid():

            problem = form.save(commit=False)

            # Gắn vào classroom hiện tại
            problem.classroom = classroom

            # Người tạo là user hiện tại
            problem.created_by = request.user

            # Problem mới luôn ở trạng thái Draft
            problem.status = 'draft'

            problem.save()

            messages.success(
                request,
                f'"{problem.title}" has been created successfully.'
            )

            return redirect(
                'problem_detail',
                problem_id=problem.id
            )

    else:

        form = ProblemForm()

    return render(
        request,
        'problems/create.html',
        {
            'form': form,
            'classroom': classroom,
        }
    )

@login_required
def import_problem_package(request, classroom_id):

    classroom = get_object_or_404(
        Classroom,
        id=classroom_id
    )

    # Teacher chỉ được import vào classroom của mình
    if (
        not request.user.is_superuser
        and classroom.teacher != request.user
    ):
        return redirect(
            'classroom_detail',
            classroom_id=classroom.id
        )

    if request.method == 'POST':

        zip_file = request.FILES.get('package_zip')
        folder_files = request.FILES.getlist('package_folder')

        try:

            # =========================================================
            # 1. IMPORT FROM ZIP
            # =========================================================
            if zip_file:

                if not zip_file.name.lower().endswith('.zip'):
                    raise ProblemPackageError(
                        'Please upload a ZIP file.'
                    )

                package_files = {}

                with zipfile.ZipFile(zip_file, 'r') as archive:

                    for info in archive.infolist():

                        if info.is_dir():
                            continue

                        normalized_name = (
                            info.filename
                            .replace('\\', '/')
                            .strip('/')
                        )

                        # Chống path traversal
                        if (
                            normalized_name.startswith('../')
                            or '/..' in normalized_name
                        ):
                            raise ProblemPackageError(
                                'ZIP package contains an invalid path.'
                            )

                        file_name = os.path.basename(
                            normalized_name
                        ).lower()

                        if file_name not in {
                            'problem.txt',
                            'input.txt',
                            'output.txt',
                        }:
                            continue

                        package_files[file_name] = archive.read(info)

            # =========================================================
            # 2. IMPORT FROM FOLDER
            # =========================================================
            elif folder_files:

                package_files = {}

                for uploaded_file in folder_files:

                    if not isinstance(uploaded_file, UploadedFile):
                        continue

                    file_name = os.path.basename(
                        uploaded_file.name
                    ).lower()

                    if file_name in {
                        'problem.txt',
                        'input.txt',
                        'output.txt',
                    }:
                        package_files[file_name] = uploaded_file.read()

            else:

                raise ProblemPackageError(
                    'Please select a ZIP file or a package folder.'
                )

            # =========================================================
            # 3. CHECK REQUIRED FILES
            # =========================================================
            required_files = {
                'problem.txt',
                'input.txt',
                'output.txt',
            }

            missing_files = (
                required_files - package_files.keys()
            )

            if missing_files:

                missing_text = ', '.join(
                    sorted(missing_files)
                )

                raise ProblemPackageError(
                    f'Missing required file(s): {missing_text}.'
                )

            # =========================================================
            # 4. PARSE + VALIDATE PACKAGE
            # =========================================================
            imported_data = validate_package(
                package_files['problem.txt'],
                package_files['input.txt'],
                package_files['output.txt'],
            )

            # =========================================================
            # 5. CREATE PROBLEM + TEST CASES
            # =========================================================
            with transaction.atomic():

                problem = Problem.objects.create(
                    classroom=classroom,
                    title=imported_data.title,
                    description=imported_data.description,
                    input_description=imported_data.input_description,
                    output_description=imported_data.output_description,
                    constraints=imported_data.constraints,
                    difficulty=imported_data.difficulty,
                    status='draft',
                    time_limit=imported_data.time_limit,
                    memory_limit=imported_data.memory_limit,
                    created_by=request.user,
                )

                TestCase.objects.bulk_create([
                    TestCase(
                        problem=problem,
                        input_data=test_case['input_data'],
                        expected_output=test_case['expected_output'],
                        is_sample=test_case['is_sample'],
                    )
                    for test_case in imported_data.test_cases
                ])

            # =========================================================
            # 6. SUCCESS
            # =========================================================
            messages.success(
                request,
                f'"{problem.title}" has been imported successfully '
                f'with {len(imported_data.test_cases)} test case(s).'
            )

            return redirect(
                'problem_detail',
                problem_id=problem.id
            )

        except (
            ProblemPackageError,
            zipfile.BadZipFile,
        ) as error:

            if isinstance(error, zipfile.BadZipFile):

                error_message = (
                    'The uploaded ZIP file is invalid or corrupted.'
                )

            else:

                error_message = str(error)

            messages.error(
                request,
                error_message
            )

    return render(
        request,
        'problems/import.html',
        {
            'classroom': classroom,
        }
    )


@login_required
def export_problem_package(request, problem_id):

    problem = get_object_or_404(
        Problem,
        id=problem_id
    )

    classroom = problem.classroom

    # =========================================================
    # PERMISSION
    # =========================================================

    if (
        not request.user.is_superuser
        and classroom.teacher != request.user
    ):
        return redirect(
            'problem_detail',
            problem_id=problem.id
        )

    # =========================================================
    # BUILD ZIP
    # =========================================================

    try:

        from .services.package_exporter import (
            build_problem_package,
        )

        package_bytes, filename = (
            build_problem_package(problem)
        )

    except ProblemPackageError as error:

        messages.error(
            request,
            str(error)
        )

        return redirect(
            'problem_detail',
            problem_id=problem.id
        )

    # =========================================================
    # RESPONSE
    # =========================================================

    response = HttpResponse(
        package_bytes,
        content_type='application/zip'
    )

    response[
        'Content-Disposition'
    ] = (
        'attachment; '
        f'filename="{filename}"'
    )

    return response

@login_required
def edit_problem(request, problem_id):

    problem = get_object_or_404(
        Problem.objects.select_related(
            'classroom',
            'created_by'
        ),
        id=problem_id
    )

    classroom = problem.classroom

    # =========================================================
    # PERMISSION
    # Teacher phải là chủ classroom
    # Admin được phép chỉnh sửa
    # =========================================================

    if (
        not request.user.is_superuser
        and classroom.teacher != request.user
    ):
        return redirect(
            'problem_detail',
            problem_id=problem.id
        )

    # =========================================================
    # POST
    # =========================================================

    if request.method == 'POST':

        form = ProblemForm(
            request.POST,
            instance=problem
        )

        formset = TestCaseFormSet(
            request.POST,
            instance=problem
        )

        if form.is_valid() and formset.is_valid():

            with transaction.atomic():

                # =============================================
                # UPDATE PROBLEM
                # =============================================

                updated_problem = form.save(commit=False)

                # Không cho phép thay đổi classroom
                updated_problem.classroom = classroom

                # Không thay đổi người tạo
                updated_problem.created_by = problem.created_by

                # Không thay đổi status
                updated_problem.status = problem.status

                updated_problem.save()

                # =============================================
                # UPDATE / CREATE / DELETE TEST CASES
                # =============================================

                formset.instance = updated_problem
                formset.save()

            messages.success(
                request,
                f'"{updated_problem.title}" has been updated successfully.'
            )

            return redirect(
                'problem_detail',
                problem_id=updated_problem.id
            )

    # =========================================================
    # GET
    # =========================================================

    else:

        form = ProblemForm(
            instance=problem
        )

        formset = TestCaseFormSet(
            instance=problem
        )

    # =========================================================
    # RENDER
    # =========================================================

    return render(
        request,
        'problems/edit.html',
        {
            'form': form,
            'formset': formset,
            'problem': problem,
            'classroom': classroom,
        }
    )


