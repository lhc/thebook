import datetime
import decimal

import pytest
from model_bakery import baker

from thebook.bookkeeping.models import BankAccount, Document, Transaction


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


def test_transaction_without_linked_document(db):
    transaction = baker.make(Transaction)

    assert transaction.has_documents is False


def test_transaction_with_linked_document(db):
    transaction = baker.make(Transaction)
    document = baker.make(Document, transaction=transaction)

    assert transaction.has_documents is True


def test_transaction_related_name_for_bank_account(db):
    bank_account = BankAccount.objects.create(name="Test Bank Account")

    transaction_1 = baker.make(Transaction, bank_account=bank_account)
    transaction_2 = baker.make(Transaction, bank_account=bank_account)
    transaction_3 = baker.make(Transaction)

    transactions = bank_account.transactions.all()
    assert transaction_1 in transactions
    assert transaction_2 in transactions
    assert transaction_3 not in transactions


def test_transaction_related_query_name_for_bank_account(db):
    bank_account_1 = BankAccount.objects.create(name="Test Bank Account 1")
    bank_account_2 = BankAccount.objects.create(name="Test Bank Account 2")

    transaction_1 = baker.make(
        Transaction, description="income", bank_account=bank_account_1
    )
    transaction_2 = baker.make(
        Transaction, description="expense", bank_account=bank_account_2
    )
    transaction_1 = baker.make(
        Transaction, description="income", bank_account=bank_account_1
    )

    bank_accounts = BankAccount.objects.filter(transaction__description="expense")
    assert len(bank_accounts) == 1

    assert bank_account_1 not in bank_accounts
    assert bank_account_2 in bank_accounts


def test_transactions_with_cash_book_info__income_and_expense(db):
    transaction_1 = baker.make(
        Transaction, date=datetime.date(2026, 2, 5), amount=decimal.Decimal("42.12")
    )
    transaction_2 = baker.make(
        Transaction, date=datetime.date(2026, 2, 6), amount=decimal.Decimal("-35.45")
    )

    transactions = Transaction.objects.with_info_for_cash_book()

    assert len(transactions) == 2

    assert transactions[0].id == transaction_1.id
    assert transactions[0].income == decimal.Decimal("42.12")
    assert transactions[0].expense is None

    assert transactions[1].id == transaction_2.id
    assert transactions[1].income is None
    assert transactions[1].expense == decimal.Decimal("-35.45")


def test_transactions_with_cash_book_info__accumulative_balance(db):
    transaction_1 = baker.make(
        Transaction, date=datetime.date(2026, 2, 5), amount=decimal.Decimal("42.12")
    )
    transaction_2 = baker.make(
        Transaction, date=datetime.date(2026, 2, 6), amount=decimal.Decimal("-35.45")
    )
    transaction_3 = baker.make(
        Transaction, date=datetime.date(2026, 2, 7), amount=decimal.Decimal("1.50")
    )

    transactions = Transaction.objects.with_info_for_cash_book()

    assert len(transactions) == 3

    assert transactions[0].id == transaction_1.id
    assert transactions[0].balance == pytest.approx(decimal.Decimal("42.12"))

    assert transactions[1].id == transaction_2.id
    assert transactions[1].balance == pytest.approx(decimal.Decimal("6.67"))

    assert transactions[2].id == transaction_3.id
    assert transactions[2].balance == pytest.approx(decimal.Decimal("8.17"))


def test_transactions_with_cash_book_info__accumulative_balance_plus_reference_value(
    db,
):
    transaction_1 = baker.make(
        Transaction, date=datetime.date(2026, 2, 5), amount=decimal.Decimal("42.12")
    )
    transaction_2 = baker.make(
        Transaction, date=datetime.date(2026, 2, 6), amount=decimal.Decimal("-35.45")
    )
    transaction_3 = baker.make(
        Transaction, date=datetime.date(2026, 2, 7), amount=decimal.Decimal("1.50")
    )

    transactions = Transaction.objects.with_info_for_cash_book(
        base_value=decimal.Decimal("100")
    )

    assert len(transactions) == 3

    assert transactions[0].id == transaction_1.id
    assert transactions[0].balance == pytest.approx(decimal.Decimal("142.12"))

    assert transactions[1].id == transaction_2.id
    assert transactions[1].balance == pytest.approx(decimal.Decimal("106.67"))

    assert transactions[2].id == transaction_3.id
    assert transactions[2].balance == pytest.approx(decimal.Decimal("108.17"))
