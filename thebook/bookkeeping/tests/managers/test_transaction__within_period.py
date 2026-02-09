import datetime

from model_bakery import baker

from thebook.bookkeeping.models import Transaction


def test_get_transactions_with_period(db):

    transaction_1 = baker.make(Transaction, date=datetime.date(2025, 9, 30))
    transaction_2 = baker.make(Transaction, date=datetime.date(2025, 10, 1))
    transaction_3 = baker.make(Transaction, date=datetime.date(2025, 11, 1))
    transaction_4 = baker.make(Transaction, date=datetime.date(2025, 11, 14))
    transaction_5 = baker.make(Transaction, date=datetime.date(2025, 11, 15))
    transaction_6 = baker.make(Transaction, date=datetime.date(2025, 11, 16))

    transactions = Transaction.objects.within_period(
        start_date=datetime.date(2025, 10, 1),
        end_date=datetime.date(2025, 11, 15),
    )

    assert transaction_1 not in transactions
    assert transaction_2 in transactions
    assert transaction_3 in transactions
    assert transaction_4 in transactions
    assert transaction_5 in transactions
    assert transaction_6 not in transactions
