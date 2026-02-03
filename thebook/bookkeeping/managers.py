import datetime
import decimal
from dataclasses import dataclass

from django.db import models
from django.db.models import DateField, Exists, IntegerField, OuterRef, Q, Sum, Value


class BankAccountQuerySet(models.QuerySet):

    def with_summary(self, start_date, end_date):
        incomes_filters = {
            "transaction__amount__gte": 0,
            "transaction__date__gte": start_date,
            "transaction__date__lt": end_date,
        }
        expenses_filters = {
            "transaction__amount__lt": 0,
            "transaction__date__gte": start_date,
            "transaction__date__lt": end_date,
        }
        period_balance_filter = {
            "transaction__date__gte": start_date,
            "transaction__date__lt": end_date,
        }

        return self.annotate(
            incomes=Sum(
                "transaction__amount",
                filter=Q(**incomes_filters),
                default=decimal.Decimal("0"),
            ),
            expenses=Sum(
                "transaction__amount",
                filter=Q(**expenses_filters),
                default=decimal.Decimal("0"),
            ),
            period_balance=Sum(
                "transaction__amount",
                filter=Q(**period_balance_filter),
                default=decimal.Decimal("0"),
            ),
            overall_balance=Sum(
                "transaction__amount",
                default=decimal.Decimal("0"),
            ),
            summary_start_date=Value(start_date, output_field=DateField()),
            summary_end_date=Value(end_date, output_field=DateField()),
        )

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


class TransactionQuerySet(models.QuerySet):

    def within_period(self, start_date, end_date):
        return self.filter(date__gte=start_date, date__lt=end_date)

    def find_match_for(self, receivable_fee):
        from thebook.members.models import ReceivableFee

        transaction = None
        for (
            rule
        ) in receivable_fee.membership.receivablefeetransactionmatchrule_set.all():
            matched_transaction = (
                self.filter(
                    category__name="Contribuição Associativa",
                    amount=receivable_fee.amount,
                    description__regex=rule.pattern,
                    date__gte=receivable_fee.membership.start_date,
                )
                .exclude(
                    Exists(ReceivableFee.objects.filter(transaction=OuterRef("pk")))
                )
                .order_by("date")
                .first()
            )
            if matched_transaction:
                transaction = matched_transaction
                break

        return transaction
