from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm

from moneybook.users.forms import UserCreationForm
from moneybook.users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = (
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_staff",
    )
    list_filter = (
        "is_active",
        "is_staff",
    )
    fieldsets = (
        (None, {"fields": ["email", "password"]}),
        ("Personal", {"fields": ["first_name", "last_name"]}),
        ("Permissions", {"fields": ["is_active", "is_staff"]}),
    )
    filter_horizontal = (
        "groups",
        "user_permissions",
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ["wide"],
                "fields": ["email", "password1", "password2"],
            },
        ),
    )
    search_fields = (
        "email",
        "first_name",
    )
    ordering = (
        "first_name",
        "last_name",
        "email",
    )
    filter_horizontal = ()
