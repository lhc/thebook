from model_bakery import baker

from thebook.members.models import FeePaymentStatus, ReceivableFee


def test_return_only_unpaid_receivable_fees(db):
    rf_1 = baker.make(ReceivableFee, status=FeePaymentStatus.UNPAID)
    rf_2 = baker.make(ReceivableFee, status=FeePaymentStatus.PAID)
    rf_3 = baker.make(ReceivableFee, status=FeePaymentStatus.UNPAID)
    rf_4 = baker.make(ReceivableFee, status=FeePaymentStatus.DUE)
    rf_5 = baker.make(ReceivableFee, status=FeePaymentStatus.UNPAID)

    receivable_fees = ReceivableFee.objects.unpaid()

    assert rf_1 in receivable_fees
    assert rf_2 not in receivable_fees
    assert rf_3 in receivable_fees
    assert rf_4 not in receivable_fees
    assert rf_5 in receivable_fees


def test_return_only_due_receivable_fees(db):
    rf_1 = baker.make(ReceivableFee, status=FeePaymentStatus.DUE)
    rf_2 = baker.make(ReceivableFee, status=FeePaymentStatus.PAID)
    rf_3 = baker.make(ReceivableFee, status=FeePaymentStatus.UNPAID)
    rf_4 = baker.make(ReceivableFee, status=FeePaymentStatus.DUE)
    rf_5 = baker.make(ReceivableFee, status=FeePaymentStatus.UNPAID)

    receivable_fees = ReceivableFee.objects.due()

    assert rf_1 in receivable_fees
    assert rf_2 not in receivable_fees
    assert rf_3 not in receivable_fees
    assert rf_4 in receivable_fees
    assert rf_5 not in receivable_fees
