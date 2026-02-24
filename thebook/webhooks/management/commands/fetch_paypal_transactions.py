import datetime

from django.core.management.base import BaseCommand

from thebook.webhooks.paypal.services import fetch_bank_account_transfer_transactions


class Command(BaseCommand):
    help = "Fetch all transactions in the last 2 days"

    def handle(self, *args, **options):
        """If we miss some webhook payload, this command should ensure that we don't lose any transaction"""
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=2)

        transactions = fetch_transactions(start_date, end_date)
        for transaction in transactions:
            transaction.save()
