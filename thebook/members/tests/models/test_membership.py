import datetime
from decimal import Decimal
from thebook.members.models import (
    Membership,
    ReceivableFee,
    FeeIntervals,
    FeePaymentStatus,
)
from model_bakery import baker
import pytest
from django.db.utils import IntegrityError


def test_not_allow_receivable_fee_for_same_membership_and_month(db):
    membership = baker.make(
        Membership,
        start_date=datetime.date(2024, 1, 1),
        membership_fee_amount=Decimal("85"),
        payment_interval=FeeIntervals.MONTHLY,
    )

    ReceivableFee.objects.create(
        membership=membership,
        start_date=datetime.date(2024, 12, 1),
        due_date=datetime.date(2024, 12, 10),
        amount=membership.membership_fee_amount,
        status=FeePaymentStatus.UNPAID,
    )

    duplicated_receivable_fee = ReceivableFee(
        membership=membership,
        start_date=datetime.date(2024, 12, 1),
        due_date=datetime.date(2024, 12, 10),
        amount=membership.membership_fee_amount,
        status=FeePaymentStatus.UNPAID,
    )
    with pytest.raises(IntegrityError) as exc:
        duplicated_receivable_fee.save()


@pytest.mark.parametrize(
    ["payment_interval", "next_membership_fee_payment_date"],
    [
        (FeeIntervals.MONTHLY, datetime.date(2024, 2, 1)),
        (FeeIntervals.QUARTERLY, datetime.date(2024, 4, 1)),
        (FeeIntervals.BIANNUALLY, datetime.date(2024, 7, 1)),
        (FeeIntervals.ANNUALLY, datetime.date(2025, 1, 1)),
    ],
)
@pytest.mark.freeze_time("2024-01-15")
def test_next_membership_fee_payment_date(
    db, payment_interval, next_membership_fee_payment_date
):
    membership = baker.make(
        Membership,
        start_date=datetime.date(2024, 1, 1),
        membership_fee_amount=Decimal("85"),
        payment_interval=payment_interval,
    )

    assert (
        membership.next_membership_fee_payment_date == next_membership_fee_payment_date
    )


@pytest.mark.parametrize(
    ["payment_interval", "membership_start_date", "next_membership_fee_payment_date"],
    [
        (FeeIntervals.MONTHLY, datetime.date(2024, 1, 1), datetime.date(2024, 2, 1)),
        (FeeIntervals.MONTHLY, datetime.date(2024, 1, 15), datetime.date(2024, 2, 15)),
        (FeeIntervals.MONTHLY, datetime.date(2024, 1, 29), datetime.date(2024, 2, 29)),
        (FeeIntervals.MONTHLY, datetime.date(2024, 1, 30), datetime.date(2024, 2, 29)),
        (FeeIntervals.MONTHLY, datetime.date(2024, 1, 31), datetime.date(2024, 2, 29)),
        (FeeIntervals.QUARTERLY, datetime.date(2024, 1, 1), datetime.date(2024, 4, 1)),
        (
            FeeIntervals.QUARTERLY,
            datetime.date(2024, 1, 15),
            datetime.date(2024, 4, 15),
        ),
        (
            FeeIntervals.QUARTERLY,
            datetime.date(2024, 1, 30),
            datetime.date(2024, 4, 30),
        ),
        (
            FeeIntervals.QUARTERLY,
            datetime.date(2024, 1, 31),
            datetime.date(2024, 4, 30),
        ),
    ],
)
@pytest.mark.freeze_time("2024-01-15")
def test_next_membership_fee_payment_date_based_on_membership_start_date(
    db, payment_interval, membership_start_date, next_membership_fee_payment_date
):
    membership = baker.make(
        Membership,
        start_date=membership_start_date,
        membership_fee_amount=Decimal("85"),
        payment_interval=payment_interval,
    )

    assert (
        membership.next_membership_fee_payment_date == next_membership_fee_payment_date
    )
