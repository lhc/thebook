import datetime
from decimal import ROUND_UP, Decimal

from django.shortcuts import render

from thebook.bookkeeping.models import BankAccount
from thebook.members.models import Membership


def _get_dashboard_context():
    deposits = Decimal("0")
    withdraws = Decimal("0")
    balance = Decimal("0")
    overall_balance = Decimal("0")

    today = datetime.date.today()
    bank_accounts_summary = BankAccount.objects.filter(active=True).summary(
        year=today.year, month=today.month
    )
    for bank_account in bank_accounts_summary:
        deposits += bank_account.deposits
        withdraws += bank_account.withdraws
        balance += bank_account.balance
        overall_balance += bank_account.overall_balance

    return {
        "deposits": deposits.quantize(Decimal(".01"), rounding=ROUND_UP),
        "withdraws": withdraws.quantize(Decimal(".01"), rounding=ROUND_UP),
        "balance": balance.quantize(Decimal(".01"), rounding=ROUND_UP),
        "overall_balance": overall_balance.quantize(Decimal(".01"), rounding=ROUND_UP),
        "bank_accounts_summary": bank_accounts_summary,
        "today": today,
        "active_memberships": Membership.objects.filter(active=True).count(),
    }


def dashboard(request):
    return render(
        request,
        "base/dashboard.html",
        context=_get_dashboard_context(),
    )
