from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from django.conf import settings
from django.db import IntegrityError

from ofxparse import OfxParser
from thebook.bookkeeping.models import Category, Transaction


@dataclass
class OFXTransaction:
    dtposted: date = None
    trnamt: Decimal = None
    fitid: str = None
    memo: str = None


IGNORED_MEMOS = [
    "APLIC.INVEST FACIL",
    "APLIC.AUTOM.INVESTFACIL*",
    "RESGATE INVEST FACIL",
]


def import_transactions(ofxfile, cash_book, user):
    category, _ = Category.objects.get_or_create(
        name=settings.BOOKKEEPING_UNCATEGORIZED
    )

    for transaction in get_ofx_transactions(ofxfile):
        try:
            obj, created = Transaction.objects.get_or_create(
                reference=transaction.fitid,
                date=transaction.dtposted,
                description=transaction.memo,
                amount=transaction.trnamt,
                cash_book=cash_book,
                category=category,
                created_by=user,
            )
        except IntegrityError:
            # Avoid importing same transaction more than once
            pass


def get_ofx_transactions(ofxfile, ignored_memos=IGNORED_MEMOS):
    for transaction in get_all_ofx_transactions(ofxfile):
        if transaction.memo in ignored_memos:
            continue
        yield transaction


def get_all_ofx_transactions(ofxfile):
    # ofxfile needs to be a file-like object
    try:
        ofx = OfxParser.parse(ofxfile)

        transactions = ofx.account.statement.transactions
        for transaction in transactions:
            yield OFXTransaction(
                dtposted=transaction.date.date(),
                trnamt=transaction.amount,
                fitid=transaction.id,
                memo=transaction.memo,
            )
    except (UnicodeDecodeError, TypeError):
        from ofxtools.Parser import OFXTree

        ofxfile.seek(0)
        parser = OFXTree()
        parser.parse(ofxfile)

        transaction_stmts = parser.findall(".//STMTTRN")
        for transaction in transaction_stmts:
            ofx_transaction = OFXTransaction()

            for element in transaction.iter():
                match element.tag:
                    case "DTPOSTED":
                        ofx_transaction.dtposted = datetime.strptime(
                            element.text, "%Y%m%d%H%M%S"
                        )
                    case "TRNAMT":
                        ofx_transaction.trnamt = Decimal(element.text.replace(",", "."))
                    case "FITID":
                        ofx_transaction.fitid = element.text
                    case "MEMO":
                        ofx_transaction.memo = element.text

            yield ofx_transaction
