import datetime
import decimal

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils.text import slugify
from django.utils.translation import gettext as _

from thebook.bookkeeping.managers import CashBookQuerySet, TransactionQuerySet


class CashBook(models.Model):
    name = models.CharField(max_length=64, unique=True)
    slug = models.SlugField(max_length=64, unique=True)
    description = models.TextField(blank=True)

    objects = CashBookQuerySet.as_manager()

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def current_month_balance(self):
        today = datetime.date.today()
        current_month = today.month
        current_year = today.year

        transactions = self.transaction_set.filter(
            date__year=current_year, date__month=current_month
        )

        incomes = transactions.filter(transaction_type=Transaction.INCOME).aggregate(
            incomes=Sum("amount")
        ).get("incomes") or decimal.Decimal("0")
        expenses = transactions.filter(transaction_type=Transaction.EXPENSE).aggregate(
            expenses=Sum("amount")
        ).get("expenses") or decimal.Decimal("0")

        return incomes - expenses

    def summary(self, month, year):
        incomes = self.transaction_set.filter(
            transaction_type=Transaction.INCOME, date__month=month, date__year=year
        ).aggregate(incomes=Sum("amount")).get("incomes") or decimal.Decimal("0")

        expenses = self.transaction_set.filter(
            transaction_type=Transaction.EXPENSE, date__month=month, date__year=year
        ).aggregate(expenses=Sum("amount")).get("expenses") or decimal.Decimal("0")

        deposits = self.transaction_set.filter(
            transaction_type=Transaction.DEPOSIT, date__month=month, date__year=year
        ).aggregate(expenses=Sum("amount")).get("expenses") or decimal.Decimal("0")

        withdraws = self.transaction_set.filter(
            transaction_type=Transaction.WITHDRAW, date__month=month, date__year=year
        ).aggregate(expenses=Sum("amount")).get("expenses") or decimal.Decimal("0")

        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "incomes": incomes,
            "expenses": expenses,
            "deposits": deposits,
            "withdraws": withdraws,
            "balance": incomes + deposits + expenses + withdraws,
            "month": month,
            "year": year,
        }


class Category(models.Model):
    name = models.CharField(max_length=64, unique=True)

    class Meta:
        verbose_name_plural = _("categories")

    def __str__(self):
        return self.name


class Document(models.Model):
    transaction = models.ForeignKey(
        "bookkeeping.Transaction", on_delete=models.CASCADE, related_name="documents"
    )
    document_file = models.FileField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Transaction(models.Model):
    DEPOSIT = 1
    EXPENSE = 2
    INCOME = 3
    WITHDRAW = 4

    TRANSACTION_TYPE_CHOICES = [
        (DEPOSIT, _("Deposit")),
        (EXPENSE, _("Expense")),
        (INCOME, _("Income")),
        (WITHDRAW, _("Withdraw")),
    ]

    reference = models.CharField(max_length=32, unique=True)
    date = models.DateField()
    description = models.CharField(max_length=256)
    transaction_type = models.SmallIntegerField(choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    cash_book = models.ForeignKey(
        "bookkeeping.CashBook", on_delete=models.SET_NULL, null=True
    )
    category = models.ForeignKey(
        "bookkeeping.Category", on_delete=models.SET_NULL, null=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )

    objects = TransactionQuerySet.as_manager()

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return f"{self.description} ({self.amount:.2f})"

    def save(self, *args, **kwargs):
        if self.transaction_type in (
            self.EXPENSE,
            self.WITHDRAW,
        ):
            self.amount *= -1

        super().save(*args, **kwargs)
