import datetime
from decimal import Decimal

import pytest
from freezegun import freeze_time
from model_bakery import baker

from django.db.models import signals

from thebook.members.models import (
    FeeIntervals,
    FeePaymentStatus,
    Membership,
    ReceivableFee,
)


@pytest.fixture
def mute_signals(request):
    """Fixture to temporarily mute Django model signals."""
    _signals = [
        signals.pre_save,
        signals.post_save,
        signals.pre_delete,
        signals.post_delete,
        signals.m2m_changed,
    ]
    restore = {}
    for signal in _signals:
        # Temporarily remove the signal's receivers
        restore[signal] = signal.receivers
        signal.receivers = []

    def restore_signals():
        # Restore the signals after the test
        for signal, receivers in restore.items():
            signal.receivers = receivers

    # Add the restore function as a finalizer
    request.addfinalizer(restore_signals)


@pytest.fixture
def build_membership(db, mute_signals):
    def _build_membership(
        start_date, active=True, payment_interval=FeeIntervals.MONTHLY
    ):
        return baker.make(
            Membership,
            start_date=start_date,
            membership_fee_amount=Decimal("85"),
            payment_interval=payment_interval,
            active=active,
        )

    return _build_membership


@pytest.mark.parametrize(
    ("payment_interval"),
    (
        FeeIntervals.MONTHLY,
        FeeIntervals.QUARTERLY,
        FeeIntervals.BIANNUALLY,
        FeeIntervals.ANNUALLY,
    ),
)
def test_create_first_receivable_fee(db, build_membership, payment_interval):
    membership = build_membership(
        start_date=datetime.date(2024, 1, 10), payment_interval=payment_interval
    )

    receivable_fee = membership.create_next_receivable_fee()

    assert receivable_fee.membership == membership
    assert receivable_fee.start_date == datetime.date(2024, 1, 1)
    assert receivable_fee.due_date == datetime.date(2024, 1, 31)
    assert receivable_fee.amount == Decimal("85")
    assert receivable_fee.status == FeePaymentStatus.UNPAID


@pytest.mark.parametrize(
    (
        "membership_start_date",
        "payment_interval",
        "expected_start_date",
        "expected_due_date",
    ),
    (
        # fmt: off
        (datetime.date(2024, 1, 10), FeeIntervals.MONTHLY, datetime.date(2024, 2, 1), datetime.date(2024, 2, 29)),
        (datetime.date(2024, 4, 10), FeeIntervals.MONTHLY, datetime.date(2024, 5, 1), datetime.date(2024, 5, 31)),
        (datetime.date(2024, 12, 10), FeeIntervals.MONTHLY, datetime.date(2025, 1, 1), datetime.date(2025, 1, 31)),
        (datetime.date(2024, 1, 10), FeeIntervals.QUARTERLY, datetime.date(2024, 4, 1), datetime.date(2024, 4, 30)),
        (datetime.date(2024, 2, 10), FeeIntervals.QUARTERLY, datetime.date(2024, 5, 1), datetime.date(2024, 5, 31)),
        (datetime.date(2024, 11, 10), FeeIntervals.QUARTERLY, datetime.date(2025, 2, 1), datetime.date(2025, 2, 28)),
        (datetime.date(2024, 1, 10), FeeIntervals.BIANNUALLY, datetime.date(2024, 7, 1), datetime.date(2024, 7, 31)),
        (datetime.date(2024, 6, 10), FeeIntervals.BIANNUALLY, datetime.date(2024, 12, 1), datetime.date(2024, 12, 31)),
        (datetime.date(2024, 9, 10), FeeIntervals.BIANNUALLY, datetime.date(2025, 3, 1), datetime.date(2025, 3, 31)),
        (datetime.date(2024, 1, 10), FeeIntervals.ANNUALLY, datetime.date(2025, 1, 1), datetime.date(2025, 1, 31)),
        (datetime.date(2024, 3, 10), FeeIntervals.ANNUALLY, datetime.date(2025, 3, 1), datetime.date(2025, 3, 31)),
        # fmt: on
    ),
)
def test_create_second_receivable_fee(
    db,
    build_membership,
    membership_start_date,
    payment_interval,
    expected_start_date,
    expected_due_date,
):
    membership = build_membership(
        start_date=membership_start_date, payment_interval=payment_interval
    )
    membership.create_next_receivable_fee()

    receivable_fee = membership.create_next_receivable_fee()

    assert receivable_fee.membership == membership
    assert receivable_fee.start_date == expected_start_date
    assert receivable_fee.due_date == expected_due_date
    assert receivable_fee.amount == Decimal("85")
    assert receivable_fee.status == FeePaymentStatus.UNPAID


def test_do_not_create_receivable_fee_for_iactive_membership(db, build_membership):
    membership = build_membership(start_date=datetime.date(2024, 1, 10), active=False)

    receivable_fee = membership.create_next_receivable_fee()

    assert receivable_fee is None


def test_create_receivable_fee_without_saving_in_db(db, build_membership):
    membership = build_membership(start_date=datetime.date(2025, 9, 8))

    receivable_fee = membership.create_next_receivable_fee(commit=False)

    assert receivable_fee.pk is None


def test_create_receivable_fee_saving_in_db_by_default(db, build_membership):
    membership = build_membership(start_date=datetime.date(2025, 9, 8))

    receivable_fee = membership.create_next_receivable_fee()

    assert receivable_fee.pk is not None


def test_create_receivable_fee_saving_in_db(db, build_membership):
    membership = build_membership(start_date=datetime.date(2025, 9, 8))

    receivable_fee = membership.create_next_receivable_fee(commit=True)

    assert receivable_fee.pk is not None
