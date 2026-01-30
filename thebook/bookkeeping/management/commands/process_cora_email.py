import email
import imaplib
import io

from decouple import config

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from thebook.bookkeeping.importers import import_transactions
from thebook.bookkeeping.models import BankAccount


class Command(BaseCommand):
    help = "Check inbox for Cora OFX files and import them"

    def handle(self, *args, **options):
        cora_bank_account = BankAccount.objects.get(name="Cora")
        User = get_user_model()

        user = User.objects.get_or_create_automation_user()

        M = imaplib.IMAP4_SSL(config("CORA_EMAIL_HOST_IMAP"))
        M.login(config("CORA_EMAIL_HOST_USER"), config("CORA_EMAIL_HOST_PASSWORD"))
        M.select(mailbox="INBOX")

        typ, msgnums = M.search(None, "FROM", "naoresponda@cora.com.br")

        for msgnum in msgnums[0].split():
            typ, data = M.fetch(msgnum, "(RFC822)")
            raw_email_string = data[0][1].decode("utf-8")
            message = email.message_from_string(raw_email_string)

            for part in message.walk():
                is_attachment = part.get_filename()
                if is_attachment:
                    attachment_content = part.get_payload(decode=True)
                    ofx_file = io.BytesIO(attachment_content)
                    import_transactions(
                        ofx_file, "ofx", cora_bank_account, user, None, None
                    )

                    M.copy(msgnum, "CoraProcessed")
                    M.store(msgnum, "+FLAGS", "\\Deleted")

        M.close()
        M.logout()
