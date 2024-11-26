import datetime
from decimal import Decimal

import pytest
from freezegun import freeze_time
from model_bakery import baker

from thebook.members.models import (
    FeeIntervals,
    FeePaymentStatus,
    Membership,
    ReceivableFee,
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
    assert receivable_fee.due_date == datetime.date(2024, 12, 31)
    assert receivable_fee.amount == Decimal("85")
    assert receivable_fee.status == FeePaymentStatus.UNPAID


@pytest.mark.freeze_time("2024-11-10")
def test_create_receivable_fee_only_for_active_membership(db):
    active_membership = baker.make(
        Membership,
        payment_interval=FeeIntervals.MONTHLY,
        active=True,
    )
    inactive_membership = baker.make(
        Membership,
        payment_interval=FeeIntervals.MONTHLY,
        active=False,
    )

    receivable_fees = ReceivableFee.objects.create_for_next_month()

    assert len(receivable_fees) == 1
    receivable_fee = receivable_fees[0]

    assert receivable_fee.membership == active_membership


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


@pytest.mark.parametrize(
    ["current_date", "expected_due_date"],
    [
        ("2024-01-10", datetime.date(2024, 2, 29)),
        ("2024-02-10", datetime.date(2024, 3, 31)),
        ("2024-03-11", datetime.date(2024, 4, 30)),
        ("2024-04-12", datetime.date(2024, 5, 31)),
        ("2024-05-13", datetime.date(2024, 6, 30)),
        ("2024-06-14", datetime.date(2024, 7, 31)),
        ("2024-07-15", datetime.date(2024, 8, 31)),
        ("2024-08-16", datetime.date(2024, 9, 30)),
        ("2024-09-17", datetime.date(2024, 10, 31)),
        ("2024-10-18", datetime.date(2024, 11, 30)),
        ("2024-11-19", datetime.date(2024, 12, 31)),
        ("2024-12-20", datetime.date(2025, 1, 31)),
        ("2025-01-21", datetime.date(2025, 2, 28)),
    ],
)
def test_due_date_last_day_of_next_month(db, current_date, expected_due_date):
    membership = baker.make(
        Membership,
        start_date=datetime.date(2024, 1, 1),
        membership_fee_amount=Decimal("85"),
        payment_interval=FeeIntervals.MONTHLY,
    )
    with freeze_time(current_date):
        receivable_fees = ReceivableFee.objects.create_for_next_month()

        assert len(receivable_fees) == 1
        receivable_fee = receivable_fees[0]

        assert receivable_fee.due_date == expected_due_date
