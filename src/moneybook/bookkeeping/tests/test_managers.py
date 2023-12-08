import datetime

import pytest
from model_bakery import baker

from moneybook.bookkeeping.models import Transaction


@pytest.mark.django_db
def test_get_transactions_by_specific_year():
    transaction_2021 = baker.make(Transaction, date=datetime.date(2021, 4, 28))
    transaction_2022 = baker.make(Transaction, date=datetime.date(2022, 3, 2))
    transaction_2023 = baker.make(Transaction, date=datetime.date(2023, 12, 8))

    transactions = Transaction.objects.for_year(2022)

    assert len(transactions) == 1
    assert transaction_2021 not in transactions
    assert transaction_2022 in transactions
    assert transaction_2023 not in transactions
