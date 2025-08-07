import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from thebook.bookkeeping.models import Transaction
from thebook.members.models import FeePaymentStatus, ReceivableFee


class Command(BaseCommand):
    help = "Match unpaid receivable fees with transactions"

    def handle(self, *args, **options):
        for status in (FeePaymentStatus.DUE, FeePaymentStatus.UNPAID):
            receivable_fees = ReceivableFee.objects.filter(status=status)
            for receivable_fee in receivable_fees:
                # This is the date we started to create ReceivableFees
                # automatically, so we should ignore past transactions
                transaction = Transaction.objects.filter(
                    date__gte=datetime.date(2025, 6, 1)
                ).find_match_for(receivable_fee)
                if not transaction:
                    continue
                receivable_fee.paid_with(transaction)

        self.stdout.write(self.style.SUCCESS("Successfully matched transactions"))
