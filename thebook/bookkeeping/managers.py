import datetime
import decimal
from dataclasses import dataclass

from django.db import models
from django.db.models import F, Q, Sum, Value, Window, IntegerField


class CashBookQuerySet(models.QuerySet):
    def summary(self, *, year=None, month=None):
        def _valid_year_and_month(month, year):
            if month is not None:
                return all(
                    [
                        month in range(1, 13),
                        year is not None,
                    ]
                )
            return True

        if not _valid_year_and_month(month, year):
            raise ValueError("Invalid 'month' and 'year' arguments")

        withdraw_filters = {"transaction__amount__lt": 0}
        deposit_filters = {
            "transaction__amount__gte": 0,
        }
        balance_filter = {}

        if year is not None:
            withdraw_filters.update({"transaction__date__year": year})
            deposit_filters.update({"transaction__date__year": year})
            balance_filter.update({"transaction__date__year": year})

        if month is not None:
            withdraw_filters.update({"transaction__date__month": month})
            deposit_filters.update({"transaction__date__month": month})
            balance_filter.update({"transaction__date__month": month})

        return self.annotate(
            deposits=Sum(
                "transaction__amount",
                filter=Q(**deposit_filters),
                default=decimal.Decimal("0"),
            ),
            withdraws=Sum(
                "transaction__amount",
                filter=Q(**withdraw_filters),
                default=decimal.Decimal("0"),
            ),
            balance=Sum(
                "transaction__amount",
                filter=Q(**balance_filter),
                default=decimal.Decimal("0"),
            ),
            overall_balance=Sum(
                "transaction__amount",
                default=decimal.Decimal("0"),
            ),
            year=Value(year, output_field=IntegerField()),
            month=Value(month, output_field=IntegerField()),
        ).order_by("name")


class TransactionQuerySet(models.QuerySet): ...
