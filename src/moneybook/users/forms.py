from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm

from moneybook.users.models import User


class UserCreationForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = ("email",)
        field_classes = {}
