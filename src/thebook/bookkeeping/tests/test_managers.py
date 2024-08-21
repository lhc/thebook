import datetime
import decimal

from model_bakery import baker

from thebook.bookkeeping.models import CashBook, Transaction


def test_get_transaction_for_cash_book(db):
    cash_book_1 = baker.make(CashBook)
    cash_book_2 = baker.make(CashBook)  # noqa

    transaction_1 = baker.make(Transaction, cash_book=cash_book_1)
    transaction_2 = baker.make(Transaction, cash_book=cash_book_2)
    transaction_3 = baker.make(Transaction, cash_book=cash_book_1)

    transactions = Transaction.objects.for_cash_book(cash_book_2.slug)

    assert len(transactions) == 1
    assert transaction_1 not in transactions
    assert transaction_2 in transactions
    assert transaction_3 not in transactions


def test_transactions_with_cumulative_sum(db):
    transaction_1 = baker.make(
        Transaction, date=datetime.date(2021, 4, 28), amount=decimal.Decimal("100.1")
    )
    transaction_2 = baker.make(
        Transaction, date=datetime.date(2022, 3, 2), amount=decimal.Decimal("142")
    )
    transaction_3 = baker.make(
        Transaction, date=datetime.date(2023, 3, 2), amount=decimal.Decimal("255.55")
    )

    transactions = Transaction.objects.with_cumulative_sum()
    assert len(transactions) == 3

    assert transactions[0].id == transaction_1.id
    assert transactions[0].cumulative_sum == transaction_1.amount

    assert transactions[1].id == transaction_2.id
    assert transactions[1].cumulative_sum == transaction_1.amount + transaction_2.amount

    assert transactions[2].id == transaction_3.id
    assert (
        transactions[2].cumulative_sum
        == transaction_1.amount + transaction_2.amount + transaction_3.amount
    )


def test_transactions_summary_with_transactions(
    db, cash_book_one_with_transactions, cash_book_two_with_transactions
):
    transactions_summary = Transaction.objects.summary(month=4, year=2024)

    assert transactions_summary.deposits_month == decimal.Decimal("234.04")
    assert transactions_summary.withdraws_month == decimal.Decimal("-315.07")
    assert transactions_summary.balance_month == decimal.Decimal("-81.03")
    assert transactions_summary.balance_year == decimal.Decimal("159.87")
    assert transactions_summary.current_balance == decimal.Decimal("259.87")
    assert transactions_summary.month == 4
    assert transactions_summary.year == 2024


def test_cash_books_summary_with_transactions(
    db, cash_book_one_with_transactions, cash_book_two_with_transactions
):
    # Ordering by id to ensure that the first result is the Cash Book created in the fixture
    cash_books_summary = CashBook.objects.summary(month=4, year=2024).order_by("id")

    assert len(cash_books_summary) == 2

    first_summary = cash_books_summary[0]  # i.e. cash_book_one_with_transactions
    second_summary = cash_books_summary[1]  # i.e. cash_book_two_with_transactions

    assert first_summary.name == cash_book_one_with_transactions.name
    assert first_summary.slug == cash_book_one_with_transactions.slug
    assert first_summary.balance_month == decimal.Decimal("74.39")
    assert first_summary.current_balance == decimal.Decimal("194.39")
    assert first_summary.month == 4
    assert first_summary.year == 2024

    assert second_summary.name == cash_book_two_with_transactions.name
    assert second_summary.slug == cash_book_two_with_transactions.slug
    assert second_summary.balance_month == decimal.Decimal("-155.42")
    assert second_summary.current_balance == decimal.Decimal("65.48")
    assert second_summary.month == 4
    assert second_summary.year == 2024
