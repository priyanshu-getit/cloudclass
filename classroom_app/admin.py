# cloudclass/classroom_app/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, ClassRoom, Subject, Timetable, Attendance


class UserAdmin(BaseUserAdmin):
    """Admin panel settings for custom User model."""

    # Columns shown in the list view
    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_superuser")

    # Fields visible when editing a user
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("email",)}),
        ("Role", {"fields": ("role",)}),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
    )

    # Fields shown when creating a user
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "role", "password1", "password2"),
        }),
    )

    search_fields = ("username", "email")
    ordering = ("username",)


# Register models
admin.site.register(User, UserAdmin)
admin.site.register(UserProfile)
admin.site.register(ClassRoom)
admin.site.register(Subject)
admin.site.register(Timetable)
admin.site.register(Attendance)
