import random

from django.core.management.base import BaseCommand
from faker import Faker

from moneybook.bookkeeping.models import Account, Category, Transaction
from moneybook.users.models import User


class Command(BaseCommand):
    help = "Load database with fake data (useful for development)"

    def handle(self, *args, **options):
        accounts = Account.objects.bulk_create(
            [Account(name="Capybara Bank"), Account(name="Paypal")]
        )
        user = User.objects.create(email="testuser@fakedata.com")
        categories = Category.objects.bulk_create(
            [
                Category(name="groceries"),
                Category(name="rent"),
                Category(name="membership"),
            ]
        )

        fake = Faker()
        transactions = []
        for _ in range(30):
            transactions.append(
                Transaction(
                    date=fake.date(),
                    description=f"Payment for {fake.name()}",
                    transaction_type=random.choice(
                        [type_ for type_, _ in Transaction.TRANSACTION_TYPE_CHOICES]
                    ),
                    amount=random.randint(1, 1000),
                    notes=fake.sentence(),
                    account=random.choice(accounts),
                    category=random.choice(categories),
                    created_by=user,
                )
            )
        Transaction.objects.bulk_create(transactions)

        self.stdout.write(self.style.SUCCESS("Successfully created fake data"))
