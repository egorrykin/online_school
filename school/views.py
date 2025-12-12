from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q, Count, Avg
from django.utils import timezone
from .models import Profile, Course, Assignment, Submission, Announcement
from .forms import (
    UserRegistrationForm,
    LoginForm,
    CourseForm,
    AssignmentForm,
    SubmissionForm,
    GradeForm,
    AnnouncementForm,
    ProfileForm,
)
from django.http import JsonResponse


def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    return render(request, "home.html")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()

            role = form.cleaned_data.get("role")

            profile_exists = Profile.objects.filter(user=user).exists()

            if not profile_exists:
                Profile.objects.create(user=user, role=role)
            else:
                profile = Profile.objects.get(user=user)
                profile.role = role
                profile.save()

            login(request, user)

            messages.success(
                request, f"🎉 Добро пожаловать в Online School, {user.first_name}!"
            )
            return redirect("dashboard")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserRegistrationForm()

    return render(request, "register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f"👋 С возвращением, {user.first_name}!")
                return redirect("dashboard")
            else:
                messages.error(request, "❌ Неверное имя пользователя или пароль.")
    else:
        form = LoginForm()

    return render(request, "login.html", {"form": form})


@login_required
def logout_view(request):
    messages.info(request, "👋 Вы вышли из системы. До новых встреч!")
    logout(request)
    return redirect("home")


@login_required
def dashboard(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user, role="student")

    if profile.role == "teacher":
        return teacher_dashboard(request)
    else:
        return student_dashboard(request)


def teacher_check(user):
    try:
        return user.profile.role == "teacher"
    except Profile.DoesNotExist:
        return False


def student_check(user):
    try:
        return user.profile.role == "student"
    except Profile.DoesNotExist:
        return False


@login_required
@user_passes_test(teacher_check, login_url="/dashboard/")
def teacher_dashboard(request):
    courses = Course.objects.filter(teacher=request.user)

    assignments = Assignment.objects.filter(teacher=request.user)

    submissions_to_grade = Submission.objects.filter(
        assignment__teacher=request.user, grade__isnull=True
    ).order_by("-submitted_at")[:10]

    stats = {
        "courses_count": courses.count(),
        "assignments_count": assignments.count(),
        "students_count": User.objects.filter(
            profile__role="student", courses_enrolled__teacher=request.user
        )
        .distinct()
        .count(),
        "submissions_to_grade": submissions_to_grade.count(),
    }

    recent_announcements = Announcement.objects.filter(
        course__teacher=request.user
    ).order_by("-created_at")[:5]

    context = {
        "courses": courses,
        "assignments": assignments,
        "submissions_to_grade": submissions_to_grade,
        "stats": stats,
        "recent_announcements": recent_announcements,
    }

    return render(request, "teacher_dashboard.html", context)


@login_required
@user_passes_test(student_check, login_url="/dashboard/")
def student_dashboard(request):
    courses = request.user.courses_enrolled.all()

    active_assignments = Assignment.objects.filter(
        course__in=courses, status="published", due_date__gt=timezone.now()
    ).order_by("due_date")

    overdue_assignments = (
        Assignment.objects.filter(
            course__in=courses, status="published", due_date__lt=timezone.now()
        )
        .exclude(submissions__student=request.user)
        .order_by("due_date")
    )

    recent_submissions = Submission.objects.filter(student=request.user).order_by(
        "-submitted_at"
    )[:10]  # Увеличим до 10 для таблицы

    grades = (
        Submission.objects.filter(student=request.user, grade__isnull=False)
        .values("assignment__course__title")
        .annotate(avg_grade=Avg("grade"))
    )

    # Получаем ID заданий, которые уже сданы
    submitted_assignments = Submission.objects.filter(
        student=request.user
    ).values_list('assignment_id', flat=True)

    context = {
        "courses": courses,
        "active_assignments": active_assignments,
        "overdue_assignments": overdue_assignments,
        "recent_submissions": recent_submissions,
        "grades": grades,
        "submitted_assignments": submitted_assignments,
    }

    return render(request, "student_dashboard.html", context)

@login_required
@user_passes_test(teacher_check, login_url="/dashboard/")
def create_course(request):
    """Создание нового курса"""
    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            course.save()
            messages.success(request, "✅ Курс успешно создан!")
            return redirect("dashboard")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CourseForm()

    return render(request, "create_course.html", {"form": form})





@login_required
@user_passes_test(teacher_check, login_url="/dashboard/")
def create_assignment(request, course_id=None):
    """Создание задания"""
    course = None
    if course_id:
        course = get_object_or_404(Course, id=course_id, teacher=request.user)

    if request.method == "POST":
        form = AssignmentForm(request.POST, user=request.user)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.teacher = request.user
            assignment.save()
            messages.success(request, "✅ Задание успешно создано!")

            if course:
                return redirect("course_detail", course_id=course.id)
            else:
                return redirect("assignment_detail", assignment_id=assignment.id)
    else:
        form = AssignmentForm(user=request.user)
        if course:
            form.fields["course"].initial = course

    context = {
        "form": form,
        "selected_course": course,
    }

    return render(request, "create_assignment.html", context)


@login_required
def assignment_detail(request, assignment_id):
    """Детальная информация о задании"""
    assignment = get_object_or_404(Assignment, id=assignment_id)

    is_teacher = request.user == assignment.teacher
    is_student = (
        request.user.profile.role == "student"
        and request.user in assignment.course.students.all()
    )

    if not (is_teacher or is_student):
        messages.error(request, "❌ У вас нет доступа к этому заданию.")
        return redirect("dashboard")

    submission = None
    submission_form = None

    if is_student:
        submission = Submission.objects.filter(
            assignment=assignment, student=request.user
        ).first()

        if not submission and assignment.status == "published":
            if request.method == "POST":
                submission_form = SubmissionForm(request.POST, request.FILES)
                if submission_form.is_valid():
                    submission = submission_form.save(commit=False)
                    submission.assignment = assignment
                    submission.student = request.user
                    submission.save()
                    messages.success(request, "✅ Ваше решение отправлено!")
                    return redirect("assignment_detail", assignment_id=assignment_id)
            else:
                submission_form = SubmissionForm()

    submissions = None
    if is_teacher:
        submissions = assignment.submissions.all()

    context = {
        "assignment": assignment,
        "is_teacher": is_teacher,
        "is_student": is_student,
        "submission": submission,
        "submission_form": submission_form,
        "submissions": submissions,
    }

    return render(request, "assignment_detail.html", context)


@login_required
@user_passes_test(teacher_check, login_url="/dashboard/")
def submissions_list(request, assignment_id):
    """Список всех решений для задания (для учителя)"""
    assignment = get_object_or_404(Assignment, id=assignment_id, teacher=request.user)
    submissions = assignment.submissions.all()

    context = {
        "assignment": assignment,
        "submissions": submissions,
    }

    return render(request, "submissions.html", context)


@login_required
@user_passes_test(teacher_check, login_url="/dashboard/")
def grade_submission(request, submission_id):
    submission = get_object_or_404(
        Submission, id=submission_id, assignment__teacher=request.user
    )

    if request.method == "POST":
        form = GradeForm(request.POST, instance=submission)
        if form.is_valid():
            form.save()
            messages.success(request, f"✅ Решение оценено! Оценка: {submission.grade}")
            return redirect("submissions_list", assignment_id=submission.assignment.id)
    else:
        form = GradeForm(instance=submission)

    context = {
        "submission": submission,
        "form": form,
    }

    return render(request, "grade_assignment.html", context)


@login_required
def my_courses(request):
    """Мои курсы"""
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user, role="student")

    if profile.role == "teacher":
        courses = Course.objects.filter(teacher=request.user)
    else:
        courses = request.user.courses_enrolled.all()

    available_courses = None
    if profile.role == "student":
        available_courses = Course.objects.exclude(students=request.user).all()[:10]

    context = {
        "courses": courses,
        "available_courses": available_courses,
        "is_teacher": profile.role == "teacher",
    }

    return render(request, "my_courses.html", context)





@login_required
def profile_view(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user, role="student")

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Профиль успешно обновлен!")
            return redirect("profile")
    else:
        form = ProfileForm(instance=profile)

    context = {
        "profile": profile,
        "form": form,
    }

    return render(request, "profile.html", context)


@login_required
@user_passes_test(teacher_check, login_url="/dashboard/")
def teacher_statistics(request):
    courses_count = Course.objects.filter(teacher=request.user).count()
    assignments_count = Assignment.objects.filter(teacher=request.user).count()
    students_count = (
        User.objects.filter(
            profile__role="student", courses_enrolled__teacher=request.user
        )
        .distinct()
        .count()
    )

    courses_stats = Course.objects.filter(teacher=request.user).annotate(
        assignments_count=Count("assignments"),
        students_count=Count("students"),
        avg_grade=Avg("assignments__submissions__grade"),
    )

    monthly_stats = [
        {"month": "Янв", "avg_grade": 85},
        {"month": "Фев", "avg_grade": 88},
        {"month": "Мар", "avg_grade": 82},
        {"month": "Апр", "avg_grade": 90},
        {"month": "Май", "avg_grade": 87},
        {"month": "Июн", "avg_grade": 92},
    ]

    context = {
        "courses_count": courses_count,
        "assignments_count": assignments_count,
        "students_count": students_count,
        "courses_stats": courses_stats,
        "monthly_stats": monthly_stats,
    }

    return render(request, "teacher_statistics.html", context)


@login_required
def course_detail(request, course_id):
    try:
        course_id_int = int(course_id)
        course = get_object_or_404(Course, id=course_id_int)

        if request.user.profile.role == "teacher":
            if course.teacher != request.user:
                messages.error(request, "❌ У вас нет доступа к этому курсу.")
                return redirect("dashboard")
        else:
            if request.user not in course.students.all():
                messages.error(request, "❌ Вы не записаны на этот курс.")
                return redirect("dashboard")

        if request.method == "POST" and request.user.profile.role == "teacher":
            if "title" in request.POST and "content" in request.POST:
                title = request.POST.get("title", "").strip()
                content = request.POST.get("content", "").strip()
                post_course_id = request.POST.get("course_id", course_id)

                try:
                    announcement_course = Course.objects.get(
                        id=post_course_id, teacher=request.user
                    )

                    if title and content:
                        Announcement.objects.create(
                            title=title,
                            content=content,
                            course=announcement_course,
                            author=request.user,
                        )
                        messages.success(request, "✅ Объявление успешно создано!")
                        return redirect(
                            "course_detail", course_id=announcement_course.id
                        )
                    else:
                        messages.error(request, "❌ Заполните все поля объявления.")
                except Course.DoesNotExist:
                    messages.error(
                        request, "❌ Курс не найден или у вас нет к нему доступа."
                    )

                return redirect("course_detail", course_id=course.id)

        assignments = course.assignments.all().order_by("-created_at")
        students = course.students.all().order_by("last_name", "first_name")
        announcements = course.announcements.all().order_by("-created_at")

        total_submissions = 0
        graded_submissions = 0
        for assignment in assignments:
            total_submissions += assignment.submissions.count()
            graded_submissions += assignment.submissions.filter(
                grade__isnull=False
            ).count()

        context = {
            "course": course,
            "assignments": assignments,
            "students": students,
            "announcements": announcements,
            "total_submissions": total_submissions,
            "graded_submissions": graded_submissions,
        }

        return render(request, "course_detail.html", context)

    except (ValueError, TypeError):
        messages.error(request, "❌ Неверный ID курса.")
        return redirect("dashboard")
    except Exception as e:
        messages.error(request, f"❌ Ошибка: {str(e)}")
        return redirect("dashboard")


@login_required
def enroll_course(request, course_id):
    if not student_check(request.user):
        messages.error(request, "❌ Только ученики могут записываться на курсы.")
        return redirect("dashboard")

    course = get_object_or_404(Course, id=course_id)

    if request.method == "POST":
        if request.user in course.students.all():
            messages.warning(request, f'⚠️ Вы уже записаны на курс "{course.title}"!')
        else:
            course.students.add(request.user)
            messages.success(
                request, f'✅ Вы успешно записались на курс "{course.title}"!'
            )
        return redirect("my_courses")

    context = {
        "course": course,
    }

    return render(request, "enroll_course.html", context)


@login_required
def profile_view(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user, role="student")
        messages.info(request, "✅ Профиль создан автоматически")

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Профиль успешно обновлен!")
            return redirect("profile")
        else:
            messages.error(request, "❌ Пожалуйста, исправьте ошибки в форме.")
    else:
        form = ProfileForm(instance=profile)

    context = {
        "profile": profile,
        "form": form,
    }

    return render(request, "profile.html", context)


@login_required
def update_avatar(request):
    if request.method == "POST" and request.FILES.get("avatar"):
        try:
            profile = request.user.profile
            profile.avatar = request.FILES["avatar"]
            profile.save()
            messages.success(request, "✅ Аватар успешно обновлен!")
        except Exception as e:
            messages.error(request, f"❌ Ошибка при загрузке аватара: {str(e)}")

    return redirect("profile")
@login_required
@user_passes_test(student_check, login_url="/dashboard/")
def submit_assignment(request, assignment_id):
    """Страница сдачи задания учеником"""
    assignment = get_object_or_404(Assignment, id=assignment_id)

    # Проверяем, что ученик записан на курс
    if request.user not in assignment.course.students.all():
        messages.error(request, "❌ Вы не записаны на этот курс.")
        return redirect("dashboard")

    # Проверяем, что задание опубликовано
    if assignment.status != "published":
        messages.error(request, "❌ Это задание недоступно для сдачи.")
        return redirect("course_detail", course_id=assignment.course.id)

    # Проверяем, не просрочено ли задание
    if timezone.now() > assignment.due_date:
        messages.warning(request, "⚠️ Срок сдачи задания истёк!")

    # Получаем существующую попытку сдачи
    submission = Submission.objects.filter(
        assignment=assignment,
        student=request.user
    ).first()

    if request.method == "POST":
        form = SubmissionForm(request.POST, request.FILES)

        if form.is_valid():
            # Если уже есть попытка, обновляем её
            if submission:
                submission.content = form.cleaned_data['content']
                if form.cleaned_data.get('file'):
                    submission.file = form.cleaned_data['file']
                submission.submitted_at = timezone.now()
                submission.save()
                messages.success(request, "✅ Решение обновлено!")
            else:
                # Создаем новую попытку
                submission = form.save(commit=False)
                submission.assignment = assignment
                submission.student = request.user
                submission.save()
                messages.success(request, "✅ Решение успешно отправлено!")

            # Отправляем уведомление учителю
            try:
                teacher = assignment.teacher
                # Здесь можно добавить отправку email или другие уведомления
                messages.info(
                    request,
                    f"📬 Учитель {teacher.get_full_name()} получил уведомление о вашей сдаче."
                )
            except:
                pass

            return redirect("assignment_detail", assignment_id=assignment.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        # Если есть предыдущая сдача, предзаполняем форму
        if submission:
            form = SubmissionForm(instance=submission)
        else:
            form = SubmissionForm()

    # Подсчитываем время до дедлайна
    time_remaining = assignment.due_date - timezone.now()
    hours_remaining = int(time_remaining.total_seconds() // 3600)

    # Получаем информацию о курсе
    course = assignment.course

    context = {
        'assignment': assignment,
        'course': course,
        'form': form,
        'submission': submission,
        'hours_remaining': hours_remaining,
        'time_remaining': time_remaining,
        'is_overdue': assignment.is_overdue(),
        'max_file_size': 10,  # Максимальный размер файла в MB
    }

    return render(request, 'submit_assignment.html', context)


@login_required
@user_passes_test(student_check, login_url="/dashboard/")
def view_submission(request, submission_id):
    """Просмотр отправленного решения"""
    submission = get_object_or_404(Submission, id=submission_id)

    # Проверяем, что ученик имеет доступ к этому решению
    if submission.student != request.user:
        messages.error(request, "❌ У вас нет доступа к этому решению.")
        return redirect("dashboard")

    assignment = submission.assignment
    course = assignment.course

    context = {
        'submission': submission,
        'assignment': assignment,
        'course': course,
    }

    return render(request, 'view_submission.html', context)