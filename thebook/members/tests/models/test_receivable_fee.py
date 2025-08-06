from model_bakery import baker

from thebook.members.models import FeePaymentStatus, ReceivableFee


def test_paid_with_transaction(db):
    transaction = baker.make("bookkeeping.Transaction")
    rf = baker.make(ReceivableFee, status=FeePaymentStatus.UNPAID)

    assert rf.status == FeePaymentStatus.UNPAID
    assert rf.transaction is None

    rf = rf.paid_with(transaction)

    assert rf.status == FeePaymentStatus.PAID
    assert rf.transaction == transaction
