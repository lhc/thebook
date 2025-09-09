import calendar
import datetime

from django.db import models


class ReceivableFeeManager(models.Manager):

    def create_for_next_month(self):
        return self.create_for_next_period()

    def create_for_next_period(self):
        from thebook.members.models import FeePaymentStatus, Membership

        receivable_fees = []

        memberships = Membership.objects.filter(active=True)
        for membership in memberships:
            receivable_fees.append(self.create_for_next_period(commit=False))

        return self.model.objects.bulk_create(
            receivable_fees,
            update_conflicts=True,
            update_fields=["membership", "start_date"],
            unique_fields=["membership", "start_date"],
        )

    def _by_status(self, status):
        return self.filter(status=status)

    def due(self):
        from thebook.members.models import FeePaymentStatus

        return self._by_status(status=FeePaymentStatus.DUE)

    def unpaid(self):
        from thebook.members.models import FeePaymentStatus

        return self._by_status(status=FeePaymentStatus.UNPAID)
