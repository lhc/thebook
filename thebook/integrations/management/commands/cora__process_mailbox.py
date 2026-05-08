import email
import imaplib
import io

from decouple import config

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from thebook.bookkeeping.importers import import_transactions
from thebook.bookkeeping.models import BankAccount
from thebook.integrations.cora.services import process_mailbox


class Command(BaseCommand):
    help = "Check inbox for Cora files and import them"

    def handle(self, *args, **options):
        process_mailbox()
