from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from thebook.members.models import ReceivableFee


class Command(BaseCommand):
    help = "Create receivable fees for next month"

    def handle(self, *args, **options):
        ReceivableFee.objects.create_for_next_month()

        self.stdout.write(
            self.style.SUCCESS("Successfully created receivable fees for next month")
        )
