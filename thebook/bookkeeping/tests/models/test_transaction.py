import datetime

import pytest
from model_bakery import baker

from thebook.bookkeeping.models import Transaction


@pytest.mark.django_db
def test_default_transaction_retrieval_order_by_date_asc():
    transaction_1 = baker.make(Transaction, date=datetime.date(2023, 4, 28))
    transaction_2 = baker.make(Transaction, date=datetime.date(2023, 3, 2))
    transaction_3 = baker.make(Transaction, date=datetime.date(2023, 10, 8))
    transaction_4 = baker.make(Transaction, date=datetime.date(2023, 4, 10))

    transactions = Transaction.objects.all()

    assert transactions.count() == 4
    assert transactions[0] == transaction_2
    assert transactions[1] == transaction_4
    assert transactions[2] == transaction_1
    assert transactions[3] == transaction_3


@pytest.mark.django_db
def test_default_transaction_retrieval_order_by_date_and_by_description_asc():
    transaction_1 = baker.make(
        Transaction, description="Transaction Y", date=datetime.date(2024, 4, 28)
    )
    transaction_2 = baker.make(
        Transaction, description="Transaction B", date=datetime.date(2024, 3, 20)
    )
    transaction_3 = baker.make(
        Transaction, description="Transaction C", date=datetime.date(2024, 3, 20)
    )
    transaction_4 = baker.make(
        Transaction, description="Transaction A", date=datetime.date(2024, 3, 20)
    )

    transactions = Transaction.objects.all()

    assert transactions.count() == 4
    assert transactions[0] == transaction_4
    assert transactions[1] == transaction_2
    assert transactions[2] == transaction_3
    assert transactions[3] == transaction_1
