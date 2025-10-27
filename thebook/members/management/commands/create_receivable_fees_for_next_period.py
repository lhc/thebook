from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from thebook.members.models import ReceivableFee


class Command(BaseCommand):
    help = "Create receivable fees for next period"

    def handle(self, *args, **options):
        ReceivableFee.objects.create_for_next_period()

        self.stdout.write(
            self.style.SUCCESS("Successfully create d receivable fees for next period")
        )
