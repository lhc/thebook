import datetime
from decimal import Decimal

import pytest
from model_bakery import baker

from thebook.bookkeeping.models import Category, Transaction
from thebook.members.models import (
    FeePaymentStatus,
    Membership,
    ReceivableFee,
    ReceivableFeeTransactionMatchRule,
)


@pytest.fixture
def membership_fee_category(db):
    return Category.objects.create(name="Contribuição Associativa")


@pytest.fixture
def membership(db):
    return baker.make(
        Membership,
        start_date=datetime.date(2025, 1, 1),
        membership_fee_amount=Decimal("100.0"),
    )


@pytest.fixture
def unpaid_rf(db, membership):
    return baker.make(
        ReceivableFee,
        membership=membership,
        start_date=datetime.date(2025, 7, 1),
        due_date=datetime.date(2025, 7, 10),
        amount=Decimal("100.0"),
        status=FeePaymentStatus.UNPAID,
    )


def test_no_transaction_for_receivable_fee_available(db, unpaid_rf):
    matched_transaction = Transaction.objects.find_match_for(unpaid_rf)

    assert matched_transaction is None


def test_find_exact_transaction_match(db, unpaid_rf, membership_fee_category):
    transaction = baker.make(
        Transaction,
        date=datetime.date(2025, 7, 10),
        amount=Decimal("100.0"),
        category=membership_fee_category,
        description="Payment of membership fee",
    )
    rf_match_rule = ReceivableFeeTransactionMatchRule.objects.create(
        pattern="Payment of membership fee",
        membership=unpaid_rf.membership,
    )

    matched_transaction = Transaction.objects.find_match_for(unpaid_rf)

    assert matched_transaction == transaction


def test_ignore_if_transaction_not_in_right_category(
    db, unpaid_rf, membership_fee_category
):
    transaction = baker.make(
        Transaction,
        date=datetime.date(2025, 7, 10),
        amount=Decimal("100.0"),
        category=Category.objects.create(name="Doação"),
        description="Payment of membership fee",
    )
    rf_match_rule = ReceivableFeeTransactionMatchRule.objects.create(
        pattern="Payment of membership fee",
        membership=unpaid_rf.membership,
    )

    matched_transaction = Transaction.objects.find_match_for(unpaid_rf)

    assert matched_transaction is None


def test_ignore_if_transaction_not_right_amount(db, unpaid_rf, membership_fee_category):
    transaction = baker.make(
        Transaction,
        date=datetime.date(2025, 7, 10),
        amount=Decimal("99"),
        category=membership_fee_category,
        description="Payment of membership fee",
    )
    rf_match_rule = ReceivableFeeTransactionMatchRule.objects.create(
        pattern="Payment of membership fee",
        membership=unpaid_rf.membership,
    )

    matched_transaction = Transaction.objects.find_match_for(unpaid_rf)

    assert matched_transaction is None


def test_match_with_the_oldest_transaction(db, unpaid_rf, membership_fee_category):
    transaction_1 = baker.make(
        Transaction,
        date=datetime.date(2025, 7, 10),
        amount=Decimal("100.0"),
        category=membership_fee_category,
        description="Payment of membership fee",
    )
    transaction_2 = baker.make(
        Transaction,
        date=datetime.date(2025, 5, 10),
        amount=Decimal("100.0"),
        category=membership_fee_category,
        description="Payment of membership fee",
    )
    transaction_3 = baker.make(
        Transaction,
        date=datetime.date(2025, 6, 10),
        amount=Decimal("100.0"),
        category=membership_fee_category,
        description="Payment of membership fee",
    )
    rf_match_rule = ReceivableFeeTransactionMatchRule.objects.create(
        pattern="Payment of membership fee",
        membership=unpaid_rf.membership,
    )

    matched_transaction = Transaction.objects.find_match_for(unpaid_rf)

    assert matched_transaction == transaction_2


def test_match_only_transactions_after_membership_started(
    db, unpaid_rf, membership_fee_category
):
    membership = baker.make(
        Membership,
        start_date=datetime.date(2025, 6, 1),
        membership_fee_amount=Decimal("100.0"),
    )
    unpaid_rf.membership = membership
    unpaid_rf.save()

    transaction_1 = baker.make(
        Transaction,
        date=datetime.date(2025, 7, 10),
        amount=Decimal("100.0"),
        category=membership_fee_category,
        description="Payment of membership fee",
    )
    transaction_2 = baker.make(
        Transaction,
        date=datetime.date(2025, 5, 10),
        amount=Decimal("100.0"),
        category=membership_fee_category,
        description="Payment of membership fee",
    )

    rf_match_rule = ReceivableFeeTransactionMatchRule.objects.create(
        pattern="Payment of membership fee",
        membership=unpaid_rf.membership,
    )

    matched_transaction = Transaction.objects.find_match_for(unpaid_rf)

    assert matched_transaction == transaction_1


def test_match_with_rules_of_right_membership(db, unpaid_rf, membership_fee_category):
    transaction = baker.make(
        Transaction,
        date=datetime.date(2025, 7, 10),
        amount=Decimal("100.0"),
        category=membership_fee_category,
        description="Payment of membership fee",
    )
    rf_match_rule = ReceivableFeeTransactionMatchRule.objects.create(
        pattern="Payment of membership fee",
        membership=baker.make(
            Membership,
            start_date=datetime.date(2025, 1, 1),
        ),
    )

    matched_transaction = Transaction.objects.find_match_for(unpaid_rf)

    assert matched_transaction is None


def test_ignore_if_transaction_was_linked_to_other_receivable_fee(
    db, unpaid_rf, membership_fee_category, membership
):
    transaction = baker.make(
        Transaction,
        date=datetime.date(2025, 6, 10),
        amount=Decimal("100"),
        category=membership_fee_category,
        description="Payment of membership fee",
    )
    other_rf = baker.make(
        ReceivableFee,
        membership=membership,
        start_date=datetime.date(2025, 6, 1),
        due_date=datetime.date(2025, 6, 10),
        amount=Decimal("100.0"),
        status=FeePaymentStatus.UNPAID,
    )
    other_rf.paid_with(transaction)

    rf_match_rule = ReceivableFeeTransactionMatchRule.objects.create(
        pattern="Payment of membership fee",
        membership=unpaid_rf.membership,
    )

    matched_transaction = Transaction.objects.find_match_for(unpaid_rf)

    assert matched_transaction is None
