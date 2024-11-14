import datetime

from django.db import models


class ReceivableFeeManager(models.Manager):
    def create_for_next_month(self):
        from thebook.members.models import Membership, FeePaymentStatus

        today = datetime.date.today()

        next_month = today.month + 1 if today.month < 12 else 1
        next_year = today.year + 1 if today.month == 12 else today.year

        receivable_fees = []

        memberships = Membership.objects.all()
        for membership in memberships:
            due_date = membership.next_membership_fee_payment_date
            if (due_date.year, due_date.month) != (next_year, next_month):
                continue

            start_date = datetime.date(due_date.year, due_date.month, 1)

            receivable_fees.append(
                self.model(
                    membership=membership,
                    start_date=start_date,
                    due_date=due_date,
                    amount=membership.membership_fee_amount,
                    status=FeePaymentStatus.UNPAID,
                )
            )
        return self.model.objects.bulk_create(
            receivable_fees,
            update_conflicts=True,
            update_fields=["membership", "start_date"],
            unique_fields=["membership", "start_date"],
        )