from django.core.management.base import BaseCommand

from thebook.bookkeeping.models import Document


class Command(BaseCommand):
    help = "Update contenty type of existing documents with the linked transactions (when set)"

    def handle(self, *args, **options):
        documents = Document.objects.filter(transaction__isnull=False)
        self.stdout.write(f"Updating content types of {len(documents)}")
        for document in documents:
            document.content_object = document.transaction
            document.save()
        self.stdout.write(f"DONE")
