import datetime
from decimal import Decimal

import pytest

from model_bakery import baker
from freezegun import freeze_time
from thebook.members.models import (
    Membership,
    ReceivableFee,
    FeeIntervals,
    FeePaymentStatus,
)


@pytest.mark.freeze_time("2024-11-10")
def test_create_receivable_fee_for_next_month(db):
    membership = baker.make(
        Membership,
        start_date=datetime.date(2024, 1, 1),
        membership_fee_amount=Decimal("85"),
        payment_interval=FeeIntervals.MONTHLY,
    )

    receivable_fees = ReceivableFee.objects.create_for_next_month()

    assert len(receivable_fees) == 1
    receivable_fee = receivable_fees[0]

    assert receivable_fee.membership == membership
    assert receivable_fee.start_date == datetime.date(2024, 12, 1)
    assert receivable_fee.due_date == datetime.date(2024, 12, 1)
    assert receivable_fee.amount == Decimal("85")
    assert receivable_fee.status == FeePaymentStatus.UNPAID


@pytest.mark.freeze_time("2024-11-10")
def test_do_not_duplicate_receivable_fees_for_same_membership(db):
    membership = baker.make(
        Membership,
        start_date=datetime.date(2024, 1, 1),
        membership_fee_amount=Decimal("85"),
        payment_interval=FeeIntervals.MONTHLY,
    )
    ReceivableFee.objects.create_for_next_month()
    ReceivableFee.objects.create_for_next_month()

    assert ReceivableFee.objects.count() == 1


@pytest.mark.parametrize(
    ["current_date", "expected_receivable_fee"],
    [
        ("2024-02-01", 1),
        ("2024-03-01", 1),
        ("2024-04-01", 1),
        ("2024-05-01", 1),
        ("2024-06-01", 1),
        ("2024-07-01", 1),
        ("2024-08-01", 1),
        ("2024-09-01", 1),
        ("2024-10-01", 1),
        ("2024-11-01", 1),
        ("2024-12-01", 1),
        ("2025-01-01", 1),
    ],
)
def test_create_receivable_fee_for_monthly_payment_interval(
    db, current_date, expected_receivable_fee
):
    membership = baker.make(
        Membership,
        start_date=datetime.date(2024, 1, 1),
        membership_fee_amount=Decimal("85"),
        payment_interval=FeeIntervals.MONTHLY,
    )

    with freeze_time(current_date):
        receivable_fees = ReceivableFee.objects.create_for_next_month()

        assert len(receivable_fees) == expected_receivable_fee


@pytest.mark.parametrize(
    ["current_date", "expected_receivable_fee"],
    [
        ("2024-02-01", 0),
        ("2024-03-01", 1),
        ("2024-04-01", 0),
        ("2024-05-01", 0),
        ("2024-06-01", 1),
        ("2024-07-01", 0),
        ("2024-08-01", 0),
        ("2024-09-01", 1),
        ("2024-10-01", 0),
        ("2024-11-01", 0),
        ("2024-12-01", 1),
        ("2025-01-01", 0),
    ],
)
def test_create_receivable_fee_for_quarterly_payment_interval(
    db, current_date, expected_receivable_fee
):
    membership = baker.make(
        Membership,
        start_date=datetime.date(2024, 1, 1),
        membership_fee_amount=Decimal("85"),
        payment_interval=FeeIntervals.QUARTERLY,
    )

    with freeze_time(current_date):
        receivable_fees = ReceivableFee.objects.create_for_next_month()

        assert len(receivable_fees) == expected_receivable_fee


@pytest.mark.parametrize(
    ["current_date", "expected_receivable_fee"],
    [
        ("2024-02-01", 0),
        ("2024-03-01", 0),
        ("2024-04-01", 0),
        ("2024-05-01", 0),
        ("2024-06-01", 1),
        ("2024-07-01", 0),
        ("2024-08-01", 0),
        ("2024-09-01", 0),
        ("2024-10-01", 0),
        ("2024-11-01", 0),
        ("2024-12-01", 1),
        ("2025-01-01", 0),
    ],
)
def test_create_receivable_fee_for_biannually_payment_interval(
    db, current_date, expected_receivable_fee
):
    membership = baker.make(
        Membership,
        start_date=datetime.date(2024, 1, 1),
        membership_fee_amount=Decimal("85"),
        payment_interval=FeeIntervals.BIANNUALLY,
    )

    with freeze_time(current_date):
        receivable_fees = ReceivableFee.objects.create_for_next_month()

        assert len(receivable_fees) == expected_receivable_fee


@pytest.mark.parametrize(
    ["current_date", "expected_receivable_fee"],
    [
        ("2024-02-01", 0),
        ("2024-03-01", 0),
        ("2024-04-01", 0),
        ("2024-05-01", 0),
        ("2024-06-01", 0),
        ("2024-07-01", 0),
        ("2024-08-01", 0),
        ("2024-09-01", 0),
        ("2024-10-01", 0),
        ("2024-11-01", 0),
        ("2024-12-01", 1),
        ("2025-01-01", 0),
    ],
)
def test_create_receivable_fee_for_annually_payment_interval(
    db, current_date, expected_receivable_fee
):
    membership = baker.make(
        Membership,
        start_date=datetime.date(2024, 1, 1),
        membership_fee_amount=Decimal("85"),
        payment_interval=FeeIntervals.ANNUALLY,
    )

    with freeze_time(current_date):
        receivable_fees = ReceivableFee.objects.create_for_next_month()

        assert len(receivable_fees) == expected_receivable_fee
