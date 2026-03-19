import email
import imaplib
import io

from decouple import config

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from thebook.bookkeeping.importers import import_transactions
from thebook.bookkeeping.models import BankAccount


class Command(BaseCommand):
    help = "Check inbox for Cora OFX files and import them"

    def handle(self, *args, **options):
        user = get_user_model().objects.get_or_create_automation_user()

        M = imaplib.IMAP4_SSL(config("CORA_EMAIL_HOST_IMAP"))
        M.login(config("CORA_EMAIL_HOST_USER"), config("CORA_EMAIL_HOST_PASSWORD"))
        M.select(mailbox="INBOX")

        typ, msgnums = M.search(None, "FROM", "naoresponda@cora.com.br")

        for msgnum in msgnums[0].split():
            typ, data = M.fetch(msgnum, "(RFC822)")
            raw_email_string = data[0][1].decode("utf-8")
            message = email.message_from_string(raw_email_string)
            for part in message.walk():
                attachment_filename = part.get_filename()
                if attachment_filename is not None:
                    if attachment_filename.endswith(".ofx"):
                        file_type = "ofx"
                        bank_account, _ = BankAccount.objects.get_or_create(
                            name=settings.CORA_BANK_ACCOUNT
                        )
                    elif attachment_filename.endswith(".csv"):
                        file_type = "csv_cora_credit_card"
                        bank_account, _ = BankAccount.objects.get_or_create(
                            name=settings.CORA_CREDIT_CARD_BANK_ACCOUNT
                        )
                    else:
                        # Unable to process this attachment
                        continue

                    attachment_content = part.get_payload(decode=True)
                    file_content = io.BytesIO(attachment_content)
                    import_transactions(
                        file_content, file_type, bank_account, user, None, None
                    )

                    M.copy(msgnum, "CoraProcessed")
                    M.store(msgnum, "+FLAGS", "\\Deleted")

        M.close()
        M.logout()
