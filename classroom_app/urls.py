# cloudclass/classroom_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),

    # auth
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # dashboards
    path("dashboard/", views.dashboard_router, name="dashboard"),
    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),
    path("teacher/dashboard/", views.teacher_dashboard, name="teacher_dashboard"),

    # teacher CRUD
    path("subjects/", views.subject_list, name="subject_list"),
    path("subjects/add/", views.add_subject, name="add_subject"),
    path("classrooms/", views.classroom_list, name="classroom_list"),
    path("classrooms/add/", views.add_classroom, name="add_classroom"),
    path("timetable/teacher/", views.timetable_list_teacher, name="timetable_list_teacher"),
    path("timetable/add/", views.add_timetable, name="add_timetable"),

    # student timetable
    path("timetable/", views.timetable_list_student, name="timetable_list_student"),

    # join class (attendance + redirect to link) via POST or AJAX
    path("join/<int:pk>/", views.join_class, name="join_class"),

    # teacher attendance report
    path("attendance/report/<int:timetable_id>/", views.attendance_report, name="attendance_report"),
]
