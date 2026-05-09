import email
import imaplib
import io

from decouple import config

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from thebook.bookkeeping.importers import import_transactions
from thebook.bookkeeping.models import BankAccount, Transaction
from thebook.integrations.cora.constants import (
    CORA_BANK_ACCOUNT,
    CORA_CREDIT_CARD_BANK_ACCOUNT,
)
from thebook.integrations.cora.importers.credit_card_invoice import (
    CoraCreditCardInvoiceImporter,
)
from thebook.integrations.cora.importers.ofx import CoraOFXImporter


def process_mailbox():
    """
    Process inbox of CORA_EMAIL_HOST_USER account trying to find
    email messages containing attachments that can be imported as
    new transactions to the system.

    This strategy was created to compensate for the fact that Cora does
    not provide an API or Webhook to send us each transaction.

    After processing each file, the read email is sent to a processed
    folder avoiding it to be processed multiple times.
    """

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
                attachment_content = part.get_payload(decode=True)
                file_content = io.BytesIO(attachment_content)

                if attachment_filename.endswith(".ofx"):
                    importer = CoraOFXImporter(file_content)
                    bank_account, _ = BankAccount.objects.get_or_create(
                        name=CORA_BANK_ACCOUNT
                    )
                elif attachment_filename.endswith(".csv"):
                    importer = CoraCreditCardInvoiceImporter(file_content)
                    bank_account, _ = BankAccount.objects.get_or_create(
                        name=CORA_CREDIT_CARD_BANK_ACCOUNT
                    )
                else:
                    # Unable to process this attachment type
                    continue

                transactions = importer.get_transactions(exclude_existing=True)
                Transaction.objects.bulk_create(
                    transactions,
                    update_conflicts=True,
                    update_fields=["description", "amount"],
                    unique_fields=["reference"],
                )

                M.copy(msgnum, "CoraProcessed")
                M.store(msgnum, "+FLAGS", "\\Deleted")

    M.close()
    M.logout()
