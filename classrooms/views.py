from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST


from .forms import JoinClassroomForm
from .models import Classroom, ClassroomMember, ClassroomBan
from .forms import CreateClassroomForm






@login_required
def classroom_list(request):

    if request.user.role == 'teacher':

        classrooms = (
            Classroom.objects
            .filter(teacher=request.user)
            .select_related('teacher')
            .order_by('-created_at')
        )

    else:

        classrooms = (
            Classroom.objects
            .filter(members__student=request.user)
            .select_related('teacher')
            .order_by('-created_at')
        )

    return render(
        request,
        'classrooms/list.html',
        {
            'classrooms': classrooms,
        }
    )


@login_required
def classroom_detail(request, classroom_id):

    classroom = get_object_or_404(
        Classroom.objects.select_related('teacher'),
        id=classroom_id
    )

    # Teacher chỉ được xem lớp mình dạy
    if request.user.role == 'teacher':

        if classroom.teacher != request.user:
            return redirect('classroom_list')

    # Student chỉ được xem lớp đã tham gia
    else:

        is_member = ClassroomMember.objects.filter(
            classroom=classroom,
            student=request.user
        ).exists()

        if not is_member:
            return redirect('classroom_list')

    # ==================================================
    # PROGRAMMING PROBLEMS
    # ==================================================

    problems = classroom.problems.all()


    # ==================================================
    # CLASSROOM MEMBERS
    # ==================================================

    members = classroom.members.select_related(
        'student'
    ).all()


    # ==================================================
    # BANNED MEMBERS
    # ==================================================

    banned_members = classroom.bans.select_related(
        'student',
        'banned_by'
    ).filter(
        is_active=True
    )


    # ==================================================
    # RENDER
    # ==================================================

    return render(
        request,
        'classrooms/detail.html',
        {
            'classroom': classroom,
            'problems': problems,
            'members': members,
            'banned_members': banned_members,
        }
    )

    classroom = get_object_or_404(
        Classroom.objects.select_related('teacher'),
        id=classroom_id
    )

    # Teacher chỉ được xem lớp mình dạy
    if request.user.role == 'teacher':

        if classroom.teacher != request.user:
            return redirect('classroom_list')

    # Student chỉ được xem lớp đã tham gia
    else:

        is_member = ClassroomMember.objects.filter(
            classroom=classroom,
            student=request.user
        ).exists()

        if not is_member:
            return redirect('classroom_list')

    problems = classroom.problems.all()

    return render(
        request,
        'classrooms/detail.html',
        {
            'classroom': classroom,
            'problems': problems,
        }
    )


@login_required
def join_classroom(request):

    # Chỉ Student được Join Classroom
    if request.user.role != 'student':
        return redirect('classroom_list')

    if request.method == 'POST':

        form = JoinClassroomForm(request.POST)

        if form.is_valid():

            code = form.cleaned_data['code'].strip()

            classroom = Classroom.objects.filter(
                code__iexact=code
            ).first()

            # Classroom không tồn tại
            if not classroom:

                form.add_error(
                    'code',
                    'Classroom code not found.'
                )

            # Người dùng chính là Teacher của classroom
            elif classroom.teacher == request.user:

                form.add_error(
                    'code',
                    'You are already the teacher of this classroom.'
                )

            # Student đang bị Ban
            elif ClassroomBan.objects.filter(
                classroom=classroom,
                student=request.user,
                is_active=True
            ).exists():

                form.add_error(
                    'code',
                    'You are banned from this classroom.'
                )

            # Student đã tham gia classroom
            elif ClassroomMember.objects.filter(
                classroom=classroom,
                student=request.user
            ).exists():

                form.add_error(
                    'code',
                    'You have already joined this classroom.'
                )

            # Join thành công
            else:

                ClassroomMember.objects.create(
                    classroom=classroom,
                    student=request.user
                )

                messages.success(
                    request,
                    f'You joined "{classroom.name}" successfully.'
                )

                return redirect(
                    'classroom_detail',
                    classroom_id=classroom.id
                )

    else:

        form = JoinClassroomForm()

    return render(
        request,
        'classrooms/join.html',
        {
            'form': form,
        }
    )

    # Teacher không dùng Join Classroom
    if request.user.role != 'student':
        return redirect('classroom_list')

    if request.method == 'POST':

        form = JoinClassroomForm(request.POST)

        if form.is_valid():

            code = form.cleaned_data['code'].strip()

            classroom = Classroom.objects.filter(
                code__iexact=code
            ).first()

            if not classroom:

                form.add_error(
                    'code',
                    'Classroom code not found.'
                )

            elif classroom.teacher == request.user:

                form.add_error(
                    'code',
                    'You are already the teacher of this classroom.'
                )

            elif ClassroomMember.objects.filter(
                classroom=classroom,
                student=request.user
            ).exists():

                form.add_error(
                    'code',
                    'You have already joined this classroom.'
                )

            else:

                ClassroomMember.objects.create(
                    classroom=classroom,
                    student=request.user
                )

                messages.success(
                    request,
                    f'You joined "{classroom.name}" successfully.'
                )

                return redirect(
                    'classroom_detail',
                    classroom_id=classroom.id
                )

    else:

        form = JoinClassroomForm()

    return render(
        request,
        'classrooms/join.html',
        {
            'form': form,
        }
    )


@login_required
def create_classroom(request):

    # Chỉ Teacher được tạo lớp
    if request.user.role != 'teacher':
        return redirect('classroom_list')

    if request.method == 'POST':

        form = CreateClassroomForm(request.POST)

        if form.is_valid():

            classroom = form.save(commit=False)

            # Người tạo lớp chính là Teacher hiện tại
            classroom.teacher = request.user

            # Tạo mã lớp
            classroom.code = (
                f'{request.user.username[:4].upper()}'
                f'{Classroom.objects.count() + 1:04d}'
            )

            classroom.save()

            return redirect(
                'classroom_detail',
                classroom_id=classroom.id
            )

    else:

        form = CreateClassroomForm()

    return render(
        request,
        'classrooms/create.html',
        {
            'form': form,
        }
    )


@login_required
@require_POST
def kick_member(request, classroom_id, student_id):

    classroom = get_object_or_404(
        Classroom,
        id=classroom_id
    )

    # Chỉ Teacher sở hữu lớp hoặc Admin
    if not request.user.is_superuser and classroom.teacher != request.user:
        return redirect(
            'classroom_detail',
            classroom_id=classroom.id
        )

    member = get_object_or_404(
        ClassroomMember,
        classroom=classroom,
        student_id=student_id
    )

    # Không cho thao tác với chính Teacher
    if member.student == classroom.teacher:
        return redirect(
            'classroom_detail',
            classroom_id=classroom.id
        )

    member.delete()

    messages.success(
        request,
        f'{member.student.username} was removed from the classroom.'
    )

    return redirect(
        'classroom_detail',
        classroom_id=classroom.id
    )

    if request.method != 'POST':
        return redirect('classroom_detail', classroom_id=classroom_id)

    classroom = get_object_or_404(
        Classroom,
        id=classroom_id
    )

    # Chỉ owner hoặc Admin được quản lý member
    if not request.user.is_superuser and classroom.teacher != request.user:
        messages.error(
            request,
            'You do not have permission to manage this classroom.'
        )
        return redirect(
            'classroom_detail',
            classroom_id=classroom.id
        )

    member = get_object_or_404(
        ClassroomMember,
        classroom=classroom,
        student_id=student_id
    )

    member.delete()

    messages.success(
        request,
        f'{member.student.username} has been removed from the classroom.'
    )

    return redirect(
        'classroom_detail',
        classroom_id=classroom.id
    )


@login_required
@require_POST
def ban_member(request, classroom_id, student_id):

    classroom = get_object_or_404(
        Classroom,
        id=classroom_id
    )

    # Chỉ Teacher sở hữu lớp hoặc Admin
    if not request.user.is_superuser and classroom.teacher != request.user:
        return redirect(
            'classroom_detail',
            classroom_id=classroom.id
        )

    member = get_object_or_404(
        ClassroomMember,
        classroom=classroom,
        student_id=student_id
    )

    # Không cho Ban Teacher
    if member.student == classroom.teacher:
        return redirect(
            'classroom_detail',
            classroom_id=classroom.id
        )

    student = member.student

    # Xóa khỏi Members
    member.delete()

    # Tạo / kích hoạt Ban
    ban, created = ClassroomBan.objects.get_or_create(
        classroom=classroom,
        student=student,
        defaults={
            'banned_by': request.user,
            'is_active': True,
        }
    )

    if not created:

        ban.banned_by = request.user
        ban.is_active = True
        ban.save(
            update_fields=[
                'banned_by',
                'is_active',
            ]
        )

    messages.success(
        request,
        f'{student.username} was banned from the classroom.'
    )

    return redirect(
        'classroom_detail',
        classroom_id=classroom.id
    )

    if request.method != 'POST':
        return redirect('classroom_detail', classroom_id=classroom_id)

    classroom = get_object_or_404(
        Classroom,
        id=classroom_id
    )

    # Chỉ owner hoặc Admin
    if not request.user.is_superuser and classroom.teacher != request.user:
        messages.error(
            request,
            'You do not have permission to manage this classroom.'
        )
        return redirect(
            'classroom_detail',
            classroom_id=classroom.id
        )

    member = get_object_or_404(
        ClassroomMember,
        classroom=classroom,
        student_id=student_id
    )

    student = member.student

    # Xóa khỏi member list
    member.delete()

    # Tạo hoặc kích hoạt ban
    ban, created = ClassroomBan.objects.get_or_create(
        classroom=classroom,
        student=student,
        defaults={
            'banned_by': request.user,
            'is_active': True,
        }
    )

    if not created:
        ban.banned_by = request.user
        ban.is_active = True
        ban.unbanned_at = None
        ban.save(
            update_fields=[
                'banned_by',
                'is_active',
                'unbanned_at',
            ]
        )

    messages.success(
        request,
        f'{student.username} has been banned from the classroom.'
    )

    return redirect(
        'classroom_detail',
        classroom_id=classroom.id
    )


@login_required
@require_POST
def unban_member(request, classroom_id, student_id):

    classroom = get_object_or_404(
        Classroom,
        id=classroom_id
    )

    # Chỉ Teacher sở hữu lớp hoặc Admin
    if not request.user.is_superuser and classroom.teacher != request.user:
        return redirect(
            'classroom_detail',
            classroom_id=classroom.id
        )

    ban = get_object_or_404(
        ClassroomBan,
        classroom=classroom,
        student_id=student_id
    )

    ban.is_active = False
    ban.save(
        update_fields=['is_active']
    )

    messages.success(
        request,
        f'{ban.student.username} was unbanned.'
    )

    return redirect(
        'classroom_detail',
        classroom_id=classroom.id
    )

    if request.method != 'POST':
        return redirect('classroom_detail', classroom_id=classroom_id)

    classroom = get_object_or_404(
        Classroom,
        id=classroom_id
    )

    # Chỉ owner hoặc Admin
    if not request.user.is_superuser and classroom.teacher != request.user:
        messages.error(
            request,
            'You do not have permission to manage this classroom.'
        )
        return redirect(
            'classroom_detail',
            classroom_id=classroom.id
        )

    ban = get_object_or_404(
        ClassroomBan,
        classroom=classroom,
        student_id=student_id,
        is_active=True
    )

    ban.is_active = False
    ban.unbanned_at = timezone.now()

    ban.save(
        update_fields=[
            'is_active',
            'unbanned_at',
        ]
    )

    messages.success(
        request,
        f'{ban.student.username} has been unbanned.'
    )

    return redirect(
        'classroom_detail',
        classroom_id=classroom.id
    )