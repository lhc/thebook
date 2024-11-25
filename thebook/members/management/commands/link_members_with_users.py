from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from thebook.members.models import Member


class Command(BaseCommand):
    help = "Create user accounts for members"

    def handle(self, *args, **options):
        User = get_user_model()

        members = Member.objects.filter(user__isnull=True)
        for member in members:
            user = User.objects.filter(email=member.email).first()
            if user is None:
                user = User.objects.create_user(
                    email=member.email,
                    first_name=member.name,
                )
                user.set_unusable_password()

            member.user = user
            member.save()

        self.stdout.write(
            self.style.SUCCESS("Successfully update members user accounts")
        )
