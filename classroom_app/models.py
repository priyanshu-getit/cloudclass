from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver


# ------------------------------
# Custom User Model
# ------------------------------
class User(AbstractUser):
    USER_ROLES = (
        ("student", "Student"),
        ("teacher", "Teacher"),
    )
    role = models.CharField(max_length=10, choices=USER_ROLES, default="student")

    def __str__(self):
        return self.username


# ------------------------------
# Classroom
# ------------------------------
class ClassRoom(models.Model):
    name = models.CharField(max_length=100, unique=True)
    capacity = models.IntegerField(default=30)

    def __str__(self):
        return self.name


# ------------------------------
# Subject
# ------------------------------
class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True, null=True)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"role": "teacher"},
    )

    def __str__(self):
        return f"{self.name} ({self.code})" if self.code else self.name


# ------------------------------
# User Profile
# ------------------------------
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} Profile"


# ------------------------------
# Timetable
# ------------------------------
class Timetable(models.Model):
    DAYS = [
        ("MON", "Monday"),
        ("TUE", "Tuesday"),
        ("WED", "Wednesday"),
        ("THU", "Thursday"),
        ("FRI", "Friday"),
        ("SAT", "Saturday"),
        ("SUN", "Sunday"),
    ]

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "teacher"},
    )

    day = models.CharField(max_length=3, choices=DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()

    meeting_link = models.URLField(null=True, blank=True)

    class Meta:
        ordering = ["day", "start_time"]

    def __str__(self):
        return f"{self.subject} - {self.get_day_display()} at {self.start_time.strftime('%H:%M')}"

    # ------------------------------
    # Validation
    # ------------------------------
    def clean(self):
        # Skip validation if fields missing (prevents NoneType errors)
        if not self.start_time or not self.end_time:
            return

        # Validate time range
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time.")

        # Query other timetable entries of the same day
        qs = Timetable.objects.filter(day=self.day)

        # Exclude itself when editing
        if self.pk:
            qs = qs.exclude(pk=self.pk)

        # Find overlapping records
        overlapping = qs.filter(
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        )

        # Classroom conflict
        if overlapping.filter(classroom=self.classroom).exists():
            raise ValidationError("This classroom is already booked during this time.")

        # Teacher conflict
        if overlapping.filter(teacher=self.teacher).exists():
            raise ValidationError("This teacher is already teaching at this time.")


# ------------------------------
# Attendance
# ------------------------------
class Attendance(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "student"},
    )
    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    present = models.BooleanField(default=True)

    class Meta:
        unique_together = ("student", "timetable")

    def __str__(self):
        return f"{self.student.username} - {self.timetable}"


# ------------------------------
# Create UserProfile automatically
# ------------------------------
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
