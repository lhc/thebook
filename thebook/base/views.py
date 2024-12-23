import datetime
from decimal import ROUND_UP, Decimal

from django.shortcuts import render

from thebook.bookkeeping.models import CashBook
from thebook.members.models import Membership


def _get_dashboard_context():
    deposits = Decimal("0")
    withdraws = Decimal("0")
    balance = Decimal("0")
    overall_balance = Decimal("0")

    today = datetime.date.today()
    cash_books_summary = CashBook.objects.filter(active=True).summary(
        year=today.year, month=today.month
    )
    for cash_book in cash_books_summary:
        deposits += cash_book.deposits
        withdraws += cash_book.withdraws
        balance += cash_book.balance
        overall_balance += cash_book.overall_balance

    return {
        "deposits": deposits.quantize(Decimal(".01"), rounding=ROUND_UP),
        "withdraws": withdraws.quantize(Decimal(".01"), rounding=ROUND_UP),
        "balance": balance.quantize(Decimal(".01"), rounding=ROUND_UP),
        "overall_balance": overall_balance.quantize(Decimal(".01"), rounding=ROUND_UP),
        "cash_books_summary": cash_books_summary,
        "today": today,
        "active_memberships": Membership.objects.filter(active=True).count(),
    }


def dashboard(request):
    return render(
        request,
        "base/dashboard.html",
        context=_get_dashboard_context(),
    )
