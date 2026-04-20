from datetime import time

from django.template.loader import get_template
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import SignupForm
from .models import Attendance, ClassRoom, Subject, Timetable, User


class SecurityRegressionTests(TestCase):
    def setUp(self):
        self.room = ClassRoom.objects.create(name="Room A")
        self.other_room = ClassRoom.objects.create(name="Room B")
        self.teacher = User.objects.create_user(
            username="teacher",
            password="pass12345",
            role="teacher",
        )
        self.other_teacher = User.objects.create_user(
            username="otherteacher",
            password="pass12345",
            role="teacher",
        )
        self.student = User.objects.create_user(
            username="student",
            password="pass12345",
            role="student",
        )
        self.student.userprofile.classroom = self.room
        self.student.userprofile.save()
        self.subject = Subject.objects.create(name="Math", teacher=self.teacher)
        self.current_day = timezone.localtime().strftime("%a").upper()[:3]
        self.timetable = Timetable.objects.create(
            subject=self.subject,
            classroom=self.room,
            teacher=self.teacher,
            day=self.current_day,
            start_time=time(0, 0),
            end_time=time(23, 59, 59),
            meeting_link="https://example.com/class",
        )
        self.other_timetable = Timetable.objects.create(
            subject=self.subject,
            classroom=self.other_room,
            teacher=self.other_teacher,
            day=self.current_day,
            start_time=time(0, 0),
            end_time=time(23, 59, 59),
            meeting_link="https://example.com/other-class",
        )
        inactive_day = "TUE" if self.current_day != "TUE" else "WED"
        self.inactive_timetable = Timetable.objects.create(
            subject=self.subject,
            classroom=self.room,
            teacher=self.teacher,
            day=inactive_day,
            start_time=time(0, 0),
            end_time=time(23, 59, 59),
            meeting_link="https://example.com/inactive-class",
        )

    def test_public_signup_cannot_create_teacher(self):
        form = SignupForm(
            data={
                "username": "newteacher",
                "email": "newteacher@example.com",
                "role": "teacher",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.role, "student")

    def test_attendance_report_is_scoped_to_logged_in_teacher(self):
        self.client.login(username="teacher", password="pass12345")

        own_response = self.client.get(
            reverse("attendance_report", args=[self.timetable.id])
        )
        other_response = self.client.get(
            reverse("attendance_report", args=[self.other_timetable.id])
        )

        self.assertEqual(own_response.status_code, 200)
        self.assertEqual(other_response.status_code, 404)

    def test_student_cannot_join_class_for_another_classroom(self):
        self.client.login(username="student", password="pass12345")

        response = self.client.post(reverse("join_class", args=[self.other_timetable.id]))

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Attendance.objects.count(), 0)

    def test_teacher_cannot_join_class_for_meeting_link(self):
        self.client.login(username="teacher", password="pass12345")

        response = self.client.post(reverse("join_class", args=[self.timetable.id]))

        self.assertEqual(response.status_code, 403)
        self.assertNotContains(response, "https://example.com/class", status_code=403)

    def test_student_join_records_one_attendance(self):
        self.client.login(username="student", password="pass12345")

        first_response = self.client.post(reverse("join_class", args=[self.timetable.id]))
        second_response = self.client.post(reverse("join_class", args=[self.timetable.id]))

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(Attendance.objects.count(), 1)

    def test_student_cannot_join_class_that_is_not_live(self):
        self.client.login(username="student", password="pass12345")

        response = self.client.post(reverse("join_class", args=[self.inactive_timetable.id]))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "https://example.com/inactive-class")
        self.assertEqual(Attendance.objects.count(), 0)

    def test_subject_list_template_loads(self):
        template = get_template("classroom_app/subject_list.html")

        self.assertIsNotNone(template)

    def test_logout_requires_post(self):
        self.client.login(username="student", password="pass12345")

        get_response = self.client.get(reverse("logout"))
        post_response = self.client.post(reverse("logout"))

        self.assertEqual(get_response.status_code, 405)
        self.assertEqual(post_response.status_code, 302)
