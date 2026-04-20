# cloudclass/classroom_app/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Subject, ClassRoom, Timetable

User = get_user_model()

class SignupForm(UserCreationForm):
    role = forms.ChoiceField(choices=User.USER_ROLES)
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ("username", "email", "role", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "student"
        if commit:
            user.save()
        return user

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["name", "code"]

class ClassroomForm(forms.ModelForm):
    class Meta:
        model = ClassRoom
        fields = ["name", "capacity"]

class TimetableForm(forms.ModelForm):
    class Meta:
        model = Timetable
        fields = ["subject", "classroom", "teacher", "day", "start_time", "end_time", "meeting_link"]
        widgets = {
            "subject": forms.Select(attrs={"class": "form-control"}),
            "classroom": forms.Select(attrs={"class": "form-control"}),
            "teacher": forms.Select(attrs={"class": "form-control"}),
            "day": forms.Select(attrs={"class": "form-control"}),
            "start_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "end_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "meeting_link": forms.URLInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Restrict teachers
        self.fields["teacher"].queryset = User.objects.filter(role="teacher")
