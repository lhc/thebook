from django.core.management.base import BaseCommand, CommandError

from thebook.bookkeeping.models import CategoryMatchRule, Transaction


class Command(BaseCommand):
    help = "Automatically set a category for uncategorized transactions"

    def handle(self, *args, **options):
        uncategorized_transactions = Transaction.objects.filter(category__isnull=True)
        category_match_rules = CategoryMatchRule.objects.all()

        for transaction in uncategorized_transactions:
            transaction.categorize(rules=category_match_rules)

        self.stdout.write(self.style.SUCCESS("Successfully categorized transactions"))
