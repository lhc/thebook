from django.shortcuts import render

from moneybook.bookkeeping.models import Transaction


def transactions(request):
    transactions = Transaction.objects.values(
        "id",
        "date",
        "amount",
        "description",
        "account__name",
        "category__name",
    ).order_by("date")

    transactions_balance = 0
    for transaction in transactions:
        transactions_balance += transaction["amount"]
        transaction["balance"] = transactions_balance

    return render(
        request, "bookkeeping/transactions.html", context={"transactions": transactions}
    )
