from django.shortcuts import render

from moneybook.bookkeeping.models import Transaction


def transactions(request):
    transactions = Transaction.objects.all().order_by("date")

    return render(
        request, "bookkeeping/transactions.html", context={"transactions": transactions}
    )
