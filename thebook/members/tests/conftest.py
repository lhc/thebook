from decimal import Decimal

import pytest
from model_bakery import baker

from django.db.models import signals

from thebook.members.models import FeeIntervals, Membership


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
