import datetime

from django.core.management.base import BaseCommand

from thebook.webhooks.paypal.services import fetch_bank_account_transfer_transactions


class Command(BaseCommand):
    help = "Fetch all bank account transfers from PayPal in the last 2 days"

    def handle(self, *args, **options):
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=2)

        fetch_bank_account_transfer_transactions(start_date, end_date)
