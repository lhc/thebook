from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext as _


class UserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_("The given email must be set"))
        email = self.normalize_email(email)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)

        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))

        return self._create_user(email, password, **extra_fields)

    def get_or_create_automation_user(self):
        """
        This user must be used as the reponsible for any automatic process
        (e.g. importing transaction from a scheduled job)
        """
        User = self.model
        automation_user_email = "batman@lhc.net.br"

        try:
            automation_user = User.objects.get(email=automation_user_email)
        except User.DoesNotExist:
            automation_user = self.model(
                email=automation_user_email,
                first_name="Bruce",
                last_name="Wayne",
                is_staff=False,
                is_active=False,
            )
            automation_user.save(using=self._db)

        return automation_user
