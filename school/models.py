from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg, Count

class Profile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Ученик'),
        ('teacher', 'Учитель'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name="Роль")
    bio = models.TextField(blank=True, verbose_name="Биография")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Аватар")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def get_average_grade(self):
        """Средняя оценка ученика"""
        if self.role != 'student':
            return None

        from .models import Submission
        submissions = Submission.objects.filter(student=self.user, grade__isnull=False)
        if submissions.exists():
            avg = submissions.aggregate(Avg('grade'))['grade__avg']
            return round(avg, 1)
        return None

    def get_success_rate(self):
        """Процент выполненных заданий"""
        if self.role != 'student':
            return 0

        from .models import Assignment, Submission
        total_assignments = Assignment.objects.filter(
            course__students=self.user
        ).count()
        completed_assignments = Submission.objects.filter(
            student=self.user
        ).count()

        if total_assignments > 0:
            return round((completed_assignments / total_assignments) * 100)
        return 0

    def get_total_students(self):
        """Общее количество учеников у учителя"""
        if self.role != 'teacher':
            return 0

        return User.objects.filter(
            profile__role='student',
            courses_enrolled__teacher=self.user
        ).distinct().count()

    def get_graded_submissions(self):
        """Количество проверенных работ"""
        if self.role != 'teacher':
            return 0

        from .models import Submission
        return Submission.objects.filter(
            assignment__teacher=self.user,
            grade__isnull=False
        ).count()

    def get_courses_count(self):
        """Количество курсов"""
        if self.role == 'teacher':
            from .models import Course
            return Course.objects.filter(teacher=self.user).count()
        else:
            return self.user.courses_enrolled.count()

    def get_recent_activity_list(self):
        """Последняя активность (простой список)"""
        activities = []

        if self.role == 'student':
            from .models import Submission
            submissions = Submission.objects.filter(
                student=self.user
            ).order_by('-submitted_at')[:5]
            for submission in submissions:
                activities.append({
                    'type': 'submission',
                    'title': f'Отправлено задание: {submission.assignment.title}',
                    'date': submission.submitted_at,
                    'grade': submission.grade,
                    'course': submission.assignment.course.title
                })
        else:
            from .models import Announcement, Assignment
            announcements = Announcement.objects.filter(
                author=self.user
            ).order_by('-created_at')[:3]
            for announcement in announcements:
                activities.append({
                    'type': 'announcement',
                    'title': f'Создано объявление: {announcement.title}',
                    'date': announcement.created_at,
                    'course': announcement.course.title
                })

            assignments = Assignment.objects.filter(
                teacher=self.user
            ).order_by('-created_at')[:2]
            for assignment in assignments:
                activities.append({
                    'type': 'assignment',
                    'title': f'Создано задание: {assignment.title}',
                    'date': assignment.created_at,
                    'course': assignment.course.title
                })

        activities.sort(key=lambda x: x['date'], reverse=True)
        return activities[:5]

class Course(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название курса")
    description = models.TextField(verbose_name="Описание")
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_taught',
                                limit_choices_to={'profile__role': 'teacher'}, verbose_name="Учитель")
    students = models.ManyToManyField(User, related_name='courses_enrolled',
                                      limit_choices_to={'profile__role': 'student'},
                                      blank=True, verbose_name="Ученики")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"

class Assignment(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('published', 'Опубликовано'),
        ('closed', 'Закрыто'),
    ]

    title = models.CharField(max_length=200, verbose_name="Название задания")
    description = models.TextField(verbose_name="Описание")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments', verbose_name="Курс")
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments_created', verbose_name="Учитель")
    due_date = models.DateTimeField(verbose_name="Срок сдачи")
    max_points = models.IntegerField(default=100, verbose_name="Максимальный балл")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_overdue(self):
        return timezone.now() > self.due_date

    def __str__(self):
        return f"{self.title} - {self.course.title}"

    class Meta:
        verbose_name = "Задание"
        verbose_name_plural = "Задания"

class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions', verbose_name="Задание")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions', verbose_name="Ученик")
    content = models.TextField(verbose_name="Решение")
    file = models.FileField(upload_to='submissions/', blank=True, null=True, verbose_name="Файл")
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="Время отправки")
    grade = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Оценка")
    feedback = models.TextField(blank=True, verbose_name="Комментарий учителя")

    def is_late(self):
        return self.submitted_at > self.assignment.due_date

    def get_grade_percentage(self):
        if self.grade and self.assignment.max_points:
            return (self.grade / self.assignment.max_points) * 100
        return 0

    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"

    class Meta:
        verbose_name = "Решение"
        verbose_name_plural = "Решения"
        unique_together = ['assignment', 'student']

class Announcement(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержание")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='announcements', verbose_name="Курс")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Объявление"
        verbose_name_plural = "Объявления"
        ordering = ['-created_at']