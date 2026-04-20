# cloudclass/classroom_app/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import datetime
from .models import User, UserProfile, Subject, ClassRoom, Timetable, Attendance
from .forms import SignupForm, SubjectForm, ClassroomForm, TimetableForm


# -------------------------
# HOME
# -------------------------
def home(request):
    sample = Timetable.objects.all().order_by("day", "start_time")[:6]
    return render(request, "home.html", {"sample": sample})


# -------------------------
# SIGNUP / LOGIN / LOGOUT
# -------------------------
def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created. Please login.")
            return redirect("login")
    else:
        form = SignupForm()

    return render(request, "auth/signup.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("dashboard")
        messages.error(request, "Invalid credentials.")
    else:
        form = AuthenticationForm()

    return render(request, "auth/login.html", {"form": form})


@login_required
@require_POST
def logout_view(request):
    logout(request)
    return redirect("login")


# -------------------------
# DASHBOARD ROUTER
# -------------------------
@login_required
def dashboard_router(request):
    if request.user.role == "student":
        return redirect("student_dashboard")
    return redirect("teacher_dashboard")


# -------------------------
# STUDENT DASHBOARD
# -------------------------
@login_required
def student_dashboard(request):
    if request.user.role != "student":
        return render(request, "403.html", status=403)

    profile = getattr(request.user, "userprofile", None)
    classroom = profile.classroom if profile else None

    now = timezone.localtime()
    weekday = now.strftime("%a").upper()[:3]

    today_timetables = (
        Timetable.objects.filter(day=weekday, classroom=classroom).order_by("start_time")
        if classroom else []
    )

    next_class = None
    for t in today_timetables:
        start_dt = datetime.combine(now.date(), t.start_time)
        if timezone.make_aware(start_dt) > now:
            next_class = t
            break

    return render(
        request,
        "classroom_app/student_dashboard.html",
        {
            "classroom": classroom,
            "today_timetables": today_timetables,
            "next_class": next_class,
            "now": now,
        },
    )


# -------------------------
# TEACHER DASHBOARD
# -------------------------
@login_required
def teacher_dashboard(request):
    if request.user.role != "teacher":
        return render(request, "403.html", status=403)

    now = timezone.localtime()
    weekday = now.strftime("%a").upper()[:3]

    classes_today = Timetable.objects.filter(
        day=weekday, teacher=request.user
    ).order_by("start_time")

    return render(
        request,
        "classroom_app/teacher_dashboard.html",
        {"classes_today": classes_today},
    )


# -------------------------
# TEACHER REQUIRED DECORATOR
# -------------------------
def teacher_required(view):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != "teacher":
            return render(request, "403.html", status=403)
        return view(request, *args, **kwargs)

    wrapper.__name__ = view.__name__
    return wrapper


# -------------------------
# SUBJECT CRUD
# -------------------------
@login_required
@teacher_required
def subject_list(request):
    subjects = Subject.objects.filter(teacher=request.user)
    return render(
        request,
        "classroom_app/subject_list.html",
        {"subjects": subjects},
    )

@login_required
@teacher_required
def add_subject(request):
    if request.method == "POST":
        form = SubjectForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.teacher = request.user      # auto-assign teacher to logged-in user
            obj.save()
            messages.success(request, "Subject added.")
            return redirect("subject_list")
    else:
        form = SubjectForm()

    return render(
        request,
        "classroom_app/add_subject.html",
        {"form": form},
    )


# -------------------------
# CLASSROOM CRUD
# -------------------------
@login_required
@teacher_required
def classroom_list(request):
    rooms = ClassRoom.objects.all()
    return render(
        request,
        "classroom_app/classroom_list.html",
        {"classrooms": rooms},
    )


@login_required
@teacher_required
def add_classroom(request):
    if request.method == "POST":
        form = ClassroomForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Classroom added.")
            return redirect("classroom_list")
    else:
        form = ClassroomForm()

    return render(
        request,
        "classroom_app/add_classroom.html",
        {"form": form},
    )


# -------------------------
# TIMETABLE (TEACHER)
# -------------------------
@login_required
@teacher_required
def timetable_list_teacher(request):
    timetables = Timetable.objects.filter(
        teacher=request.user
    ).order_by("day", "start_time")

    return render(
        request,
        "classroom_app/timetable_list_teacher.html",
        {"timetables": timetables},
    )


@login_required
@teacher_required
def add_timetable(request):
    if request.method == "POST":
        form = TimetableForm(request.POST)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.teacher = request.user  # force teacher
            try:
                obj.full_clean()
                obj.save()
                messages.success(request, "Timetable added.")
                return redirect("timetable_list_teacher")
            except Exception as e:
                messages.error(request, f"Cannot save timetable: {e}")

    else:
        form = TimetableForm()

    # limit teacher dropdown
    form.fields["teacher"].queryset = User.objects.filter(id=request.user.id)

    return render(
        request,
        "classroom_app/add_timetable.html",
        {"form": form},
    )


# -------------------------
# STUDENT TIMETABLE VIEW
# -------------------------
@login_required
def timetable_list_student(request):
    profile = getattr(request.user, "userprofile", None)
    classroom = profile.classroom if profile else None
    timetables = (
        Timetable.objects.filter(classroom=classroom).order_by("day", "start_time")
        if classroom
        else []
    )
    now = timezone.localtime()

    return render(
        request,
        "classroom_app/timetable_list_student.html",
        {"timetables": timetables, "now": now, "classroom": classroom},
    )


# -------------------------
# JOIN CLASS (AUTO ATTENDANCE)
# -------------------------
@login_required
def join_class(request, pk):
    timetable = get_object_or_404(Timetable, pk=pk)
    now = timezone.localtime()
    current_day = now.strftime("%a").upper()[:3]
    current_time = now.time()

    if request.user.role != "student":
        return JsonResponse(
            {"status": "error", "message": "Only students can join classes."},
            status=403,
        )

    profile = getattr(request.user, "userprofile", None)
    if not profile or profile.classroom_id != timetable.classroom_id:
        return JsonResponse(
            {"status": "error", "message": "This class is not assigned to your classroom."},
            status=403,
        )

    if (
        timetable.day != current_day
        or current_time < timetable.start_time
        or current_time > timetable.end_time
    ):
        return JsonResponse(
            {"status": "error", "message": "Class is not live right now."}
        )

    Attendance.objects.get_or_create(
        student=request.user,
        timetable=timetable,
    )

    return JsonResponse(
        {"status": "ok", "meeting_link": timetable.meeting_link}
    )


# -------------------------
# ATTENDANCE REPORT (TEACHER)
# -------------------------
@login_required
@teacher_required
def attendance_report(request, timetable_id):
    t = get_object_or_404(Timetable, pk=timetable_id, teacher=request.user)
    records = Attendance.objects.filter(
        timetable=t
    ).order_by("-joined_at")

    return render(
        request,
        "classroom_app/attendance_report.html",
        {"timetable": t, "records": records},
    )
