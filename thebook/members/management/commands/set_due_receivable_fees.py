import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from thebook.members.models import FeePaymentStatus, ReceivableFee


class Command(BaseCommand):
    help = "Set unpaid receivable fees as due"

    def handle(self, *args, **options):
        ReceivableFee.objects.filter(
            status=FeePaymentStatus.UNPAID,
            due_date__lt=datetime.date.today(),
        ).update(status=FeePaymentStatus.DUE)

        self.stdout.write(
            self.style.SUCCESS("Successfully updated receivable fees as due")
        )
