import sqlite3
from dataclasses import dataclass
from pathlib import Path

from django.core.management.base import BaseCommand

from moneybook.bookkeeping.models import Account, Category, Transaction
from moneybook.users.models import User


@dataclass
class Entry:
    id_: int
    entry_date: str
    value: float
    account: str
    tags: str
    description: str

    @property
    def category(self):
        return self.tags

    @property
    def reference(self):
        return f"L{self.id_:05}"

    @property
    def transaction_type(self):
        if "transferencia" in self.tags:
            return Transaction.ACCOUNT_TRANSFER
        return Transaction.INCOME if self.value >= 0 else Transaction.EXPENSE


class Command(BaseCommand):
    help = "Import data from legacy financial database"

    def add_arguments(self, parser):
        parser.add_argument("db", type=str)

    def handle(self, *args, **options):
        db_path = Path(options["db"])
        self.stdout.write(self.style.SUCCESS(f"Processing database {db_path}"))

        if not db_path.is_file():
            self.stdout.write(self.style.ERROR(f"Unable to find {db_path}"))
            return

        automation_user, _ = User.objects.get_or_create(email="contato@lhc.net.br")
        accounts = {account.name: account for account in Account.objects.all()}
        categories = {category.name: category for category in Category.objects.all()}

        existing_transactions = Transaction.objects.values_list("reference", flat=True)

        transactions = []

        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        results = cursor.execute(
            """
        SELECT
            id, entry_date, value, account, tags, description
        FROM
            entry
        """
        )
        for entry in results:
            legacy_entry = Entry(*entry)

            if legacy_entry.reference in existing_transactions:
                continue

            if legacy_entry.category == "inicial":
                # We don't need to have a transaction fo the year start
                continue

            entry_account = accounts.get(legacy_entry.account)
            if entry_account is None:
                entry_account = Account.objects.create(name=legacy_entry.account)
                accounts[legacy_entry.account] = entry_account

            entry_category = categories.get(legacy_entry.category)
            if entry_category is None:
                entry_category = Category.objects.create(name=legacy_entry.category)
                categories[legacy_entry.category] = entry_category

            transactions.append(
                Transaction(
                    reference=legacy_entry.reference,
                    date=legacy_entry.entry_date,
                    description=legacy_entry.description,
                    transaction_type=legacy_entry.transaction_type,
                    amount=legacy_entry.value,
                    notes="",
                    account=entry_account,
                    category=entry_category,
                    created_by=automation_user,
                )
            )

        self.stdout.write(
            self.style.WARNING(f"Importing {len(transactions)} new transactions")
        )
        Transaction.objects.bulk_create(transactions)
        self.stdout.write(self.style.SUCCESS("Data imported"))
