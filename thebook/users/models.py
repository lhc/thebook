from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models

from thebook.users.managers import UserManager


class User(AbstractBaseUser):
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []
    USERNAME_FIELD = "email"

    first_name = models.CharField(max_length=128, blank=True)
    last_name = models.CharField(max_length=128, blank=True)
    email = models.EmailField(unique=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm):
        # This method is required so we can use Django Admin without built-in Django permissions system
        return True

    def has_module_perms(self, app_label):
        # This method is required so we can use Django Admin without built-in Django permissions system
        return True
