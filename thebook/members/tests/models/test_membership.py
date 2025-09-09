from datetime import date
from decimal import Decimal

import pytest
from freezegun import freeze_time
from model_bakery import baker

from django.db.utils import IntegrityError

from thebook.members.models import (
    FeeIntervals,
    FeePaymentStatus,
    Member,
    Membership,
    ReceivableFee,
)


def test_not_allow_receivable_fee_for_same_membership_and_month(db):
    membership = baker.make(
        Membership,
        start_date=date(2024, 1, 1),
        membership_fee_amount=Decimal("85"),
        payment_interval=FeeIntervals.MONTHLY,
    )

    ReceivableFee.objects.create(
        membership=membership,
        start_date=date(2024, 12, 1),
        due_date=date(2024, 12, 10),
        amount=membership.membership_fee_amount,
        status=FeePaymentStatus.UNPAID,
    )

    duplicated_receivable_fee = ReceivableFee(
        membership=membership,
        start_date=date(2024, 12, 1),
        due_date=date(2024, 12, 10),
        amount=membership.membership_fee_amount,
        status=FeePaymentStatus.UNPAID,
    )
    with pytest.raises(IntegrityError) as exc:
        duplicated_receivable_fee.save()


@pytest.mark.parametrize(
    ["payment_interval", "next_membership_fee_payment_date"],
    [
        (FeeIntervals.MONTHLY, date(2024, 2, 1)),
        (FeeIntervals.QUARTERLY, date(2024, 4, 1)),
        (FeeIntervals.BIANNUALLY, date(2024, 7, 1)),
        (FeeIntervals.ANNUALLY, date(2025, 1, 1)),
    ],
)
@pytest.mark.freeze_time("2024-01-15")
def test_next_membership_fee_payment_date(
    db, payment_interval, next_membership_fee_payment_date
):
    membership = baker.make(
        Membership,
        start_date=date(2024, 1, 1),
        membership_fee_amount=Decimal("85"),
        payment_interval=payment_interval,
    )

    assert (
        membership.next_membership_fee_payment_date == next_membership_fee_payment_date
    )


@pytest.mark.parametrize(
    [
        "payment_interval",
        "membership_start_date",
        "next_membership_fee_payment_date",
        "current_date",
    ],
    [
        # fmt: off
        (FeeIntervals.MONTHLY, date(2024, 1, 1), date(2024, 2, 1), "2024-01-15"),
        (FeeIntervals.MONTHLY, date(2024, 1, 15), date(2024, 2, 15), "2024-01-15"),
        (FeeIntervals.MONTHLY, date(2024, 1, 29), date(2024, 2, 29), "2024-01-15"),
        (FeeIntervals.MONTHLY, date(2024, 1, 30), date(2024, 2, 29), "2024-01-15"),
        (FeeIntervals.MONTHLY, date(2024, 1, 31), date(2024, 2, 29), "2024-01-15"),
        (FeeIntervals.QUARTERLY, date(2024, 1, 1), date(2024, 4, 1), "2024-01-15"),
        (FeeIntervals.QUARTERLY, date(2024, 1, 15), date(2024, 4, 15), "2024-01-15"),
        (FeeIntervals.QUARTERLY, date(2024, 1, 30), date(2024, 4, 30), "2024-01-15"),
        (FeeIntervals.QUARTERLY, date(2024, 1, 31), date(2024, 4, 30), "2024-01-15"),
        (FeeIntervals.MONTHLY, date(2024, 10, 15), date(2025, 1, 15), "2024-12-15"),
        (FeeIntervals.BIANNUALLY, date(2024, 10, 15), date(2025, 4, 15), "2024-12-15"),
        (FeeIntervals.ANNUALLY, date(2024, 10, 15), date(2025, 10, 15), "2024-12-15"),
        # fmt: on
    ],
)
def test_next_membership_fee_payment_date_based_on_membership_start_date(
    db,
    payment_interval,
    membership_start_date,
    next_membership_fee_payment_date,
    current_date,
):
    with freeze_time(current_date):
        membership = baker.make(
            Membership,
            start_date=membership_start_date,
            membership_fee_amount=Decimal("85"),
            payment_interval=payment_interval,
        )

        assert (
            membership.next_membership_fee_payment_date
            == next_membership_fee_payment_date
        )


def test_when_membership_is_activated_add_first_receivable_fee(db):
    membership = Membership(
        member=baker.make(Member),
        start_date=date(2025, 8, 11),
        membership_fee_amount=Decimal("85"),
        payment_interval=FeeIntervals.MONTHLY,
        active=False,
    )

    assert not membership.receivable_fees.exists()

    membership.active = True
    membership.save()

    assert membership.receivable_fees.exists()
    assert membership.receivable_fees.count() == 1
