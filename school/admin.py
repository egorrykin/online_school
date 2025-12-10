from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Profile, Course, Assignment, Submission, Announcement

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Профиль'

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff')
    list_filter = ('profile__role', 'is_staff', 'is_superuser')

    def get_role(self, obj):
        try:
            return obj.profile.get_role_display()
        except Profile.DoesNotExist:
            return "Не указано"
    get_role.short_description = 'Роль'

class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'students_count', 'created_at')
    list_filter = ('teacher', 'created_at')
    search_fields = ('title', 'description', 'teacher__username')
    filter_horizontal = ('students',)

    def students_count(self, obj):
        return obj.students.count()
    students_count.short_description = 'Количество учеников'

class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'teacher', 'due_date', 'status', 'created_at')
    list_filter = ('status', 'course', 'teacher')
    search_fields = ('title', 'description', 'course__title')

class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student', 'submitted_at', 'grade', 'is_late')
    list_filter = ('assignment__course', 'assignment', 'submitted_at')
    search_fields = ('content', 'student__username', 'assignment__title')

    def is_late(self, obj):
        return obj.is_late()
    is_late.boolean = True
    is_late.short_description = 'Опоздание'

class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'author', 'created_at')
    list_filter = ('course', 'author', 'created_at')
    search_fields = ('title', 'content', 'course__title')

# Регистрируем модели
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Announcement, AnnouncementAdmin)