from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from django.conf import settings
from django.db import IntegrityError

from ofxparse import OfxParser
from thebook.bookkeeping.models import Category, Transaction
from ofxtools.Parser import OFXTree


@dataclass
class OFXTransaction:
    dtposted: date = None
    trnamt: Decimal = None
    fitid: str = None
    checknum: str = None
    memo: str = None


class OFXImporter:
    new_transactions = []

    # List of transactions descriptions that we can ignore and not insert into the system
    ignored_memos = [
        "APLIC.INVEST FACIL",
        "APLIC.AUTOM.INVESTFACIL*",
        "RESGATE INVEST FACIL",
        "RESG.AUTOM.INVEST FACIL*",
    ]

    def __init__(self, transactions_file, cash_book, user):
        self.uncategorized, _ = Category.objects.get_or_create(
            name=settings.BOOKKEEPING_UNCATEGORIZED
        )

        self.transactions_file = transactions_file
        self.cash_book = cash_book
        self.user = user

    def _get_reference(self, fitid, checknum):
        return "-".join([field for field in (fitid, checknum) if field])

    def run(self):
        try:
            ofx_parser = OfxParser.parse(self.transactions_file)

            transactions = ofx_parser.account.statement.transactions
            for transaction in transactions:
                self.new_transactions.append(
                    Transaction(
                        reference=self._get_reference(
                            transaction.id, transaction.checknum
                        ),
                        date=transaction.date.date(),
                        description=transaction.memo,
                        amount=transaction.amount,
                        cash_book=self.cash_book,
                        category=self.uncategorized,
                        created_by=self.user,
                    )
                )
        except (UnicodeDecodeError, TypeError):
            # Some files are not so well formated so we need to use a different parse library
            self.transactions_file.seek(0)
            ofx_parser = OFXTree()
            ofx_parser.parse(self.transactions_file)

            transaction_stmts = ofx_parser.findall(".//STMTTRN")
            for transaction in transaction_stmts:
                ofx_transaction = OFXTransaction()
                for element in transaction.iter():
                    match element.tag:
                        case "DTPOSTED":
                            ofx_transaction.dtposted = datetime.strptime(
                                element.text, "%Y%m%d%H%M%S"
                            ).date()
                        case "TRNAMT":
                            ofx_transaction.trnamt = Decimal(
                                element.text.replace(",", ".")
                            )
                        case "FITID":
                            ofx_transaction.fitid = element.text
                        case "CHECKNUM":
                            ofx_transaction.checknum = element.text
                        case "MEMO":
                            ofx_transaction.memo = element.text

                self.new_transactions.append(
                    Transaction(
                        reference=self._get_reference(
                            ofx_transaction.fitid, ofx_transaction.checknum
                        ),
                        date=ofx_transaction.dtposted,
                        description=ofx_transaction.memo,
                        amount=ofx_transaction.trnamt,
                        cash_book=self.cash_book,
                        category=self.uncategorized,
                        created_by=self.user,
                    )
                )

        Transaction.objects.bulk_create(
            [
                transaction
                for transaction in self.new_transactions
                if transaction.description not in self.ignored_memos
            ],
            update_conflicts=True,
            update_fields=["description", "amount"],
            unique_fields=["reference"],
        )
