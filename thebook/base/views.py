import datetime
from decimal import Decimal

from django.shortcuts import render


def _get_dashboard_context():
    return {
        "deposits": Decimal("0"),
        "withdraws": Decimal("0"),
        "balance": Decimal("0"),
        "overall_balance": Decimal("0"),
    }


def dashboard(request):
    return render(
        request,
        "base/dashboard.html",
        context=_get_dashboard_context(),
    )
