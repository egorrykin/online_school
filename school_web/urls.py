from django.urls import path
from school import views
from django.contrib import admin
urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/avatar/", views.update_avatar, name="update_avatar"),
    path("courses/", views.my_courses, name="my_courses"),
    path("courses/create/", views.create_course, name="create_course"),
    path("courses/<int:course_id>/", views.course_detail, name="course_detail"),
    path("courses/<int:course_id>/enroll/", views.enroll_course, name="enroll_course"),
    path("courses/<int:course_id>/enroll/", views.enroll_course, name="enroll_course"),
    path("assignments/create/", views.create_assignment, name="create_assignment"),
    path('assignment/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    path('submission/<int:submission_id>/view/', views.view_submission, name='view_submission'),

    path(
        "assignments/create/<int:course_id>/",
        views.create_assignment,
        name="create_assignment_for_course",
    ),
    path(
        "assignments/<int:assignment_id>/",
        views.assignment_detail,
        name="assignment_detail",
    ),
    path(
        "assignments/<int:assignment_id>/submissions/",
        views.submissions_list,
        name="submissions_list",
    ),
    path(
        "submissions/<int:submission_id>/grade/",
        views.grade_submission,
        name="grade_submission",
    ),
    path("statistics/", views.teacher_statistics, name="teacher_statistics"),

    path('admin/', admin.site.urls),
    ]