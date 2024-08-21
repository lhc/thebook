import datetime
import decimal

import pytest
from django.db import IntegrityError
from django.utils.text import slugify
from model_bakery import baker

from thebook.bookkeeping.models import CashBook, Transaction


@pytest.mark.django_db
def test_default_transaction_retrieval_order_by_date_asc():
    transaction_1 = baker.make(Transaction, date=datetime.date(2023, 4, 28))
    transaction_2 = baker.make(Transaction, date=datetime.date(2023, 3, 2))
    transaction_3 = baker.make(Transaction, date=datetime.date(2023, 10, 8))
    transaction_4 = baker.make(Transaction, date=datetime.date(2023, 4, 10))

    transactions = Transaction.objects.all()

    assert transactions[0] == transaction_2
    assert transactions[1] == transaction_4
    assert transactions[2] == transaction_1
    assert transactions[3] == transaction_3


@pytest.mark.django_db
def test_each_transaction_need_a_unique_reference_value():
    transaction_reference = "123456A"
    transaction_1 = baker.make(Transaction, reference=transaction_reference)  # noqa

    with pytest.raises(IntegrityError):
        transaction_2 = baker.prepare(
            Transaction, reference=transaction_reference, _save_related=True
        )
        transaction_2.save()


@pytest.mark.django_db
@pytest.mark.parametrize("cash_book_name", ["Paypal Account", "Bank", "Cash Account"])
def test_set_cash_book_slug_based_in_name(cash_book_name):
    cash_book = CashBook(name=cash_book_name)

    cash_book.save()

    assert cash_book.slug == slugify(cash_book_name)


@pytest.mark.freeze_time("2024-04-12")
def test_cash_book_summary_with_transactions(db, cash_book_one_with_transactions):
    # Income and Expense of Cash Book different than the fixture
    extra_deposit = baker.make(  # noqa
        Transaction,
        date=datetime.date(2024, 4, 2),
        amount=decimal.Decimal("15"),
    )
    extra_withdraw = baker.make(  # noqa
        Transaction,
        date=datetime.date(2024, 4, 2),
        amount=decimal.Decimal("-17.1"),
    )

    cash_book_summary = cash_book_one_with_transactions.summary(month=4, year=2024)

    assert cash_book_summary == {
        "id": cash_book_one_with_transactions.id,
        "name": cash_book_one_with_transactions.name,
        "slug": cash_book_one_with_transactions.slug,
        "deposits": decimal.Decimal("234.04"),
        "withdraws": decimal.Decimal("-159.65"),
        "balance": decimal.Decimal("74.39"),
        "month": 4,
        "year": 2024,
    }
