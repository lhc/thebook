from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from thebook.bookkeeping.models import CashBook
from thebook.bookkeeping.ofx_import import import_transactions


def cash_books(request):
    return render(request, "bookkeeping/cashbooks.html")


def all_transactions(request):
    return HttpResponse("All transactions")


def cash_book_transactions(request, cash_book_slug):
    cash_book = CashBook.objects.get(slug=cash_book_slug)
    year = request.GET.get("year") or None
    month = request.GET.get("month") or None

    transactions = cash_book.transaction_set.all().select_related("category")
    if month is not None and year is not None:
        transactions = transactions.for_period(month, year)

    initial_balance = 0

    return render(
        request,
        "bookkeeping/transactions.html",
        context={
            "cash_book": cash_book,
            "initial_balance": initial_balance,
            "transactions": transactions.with_cumulative_sum(),
        },
    )


def import_ofx(request):
    """
    This is a temporary view that imports the content of a OFX file
    and converts it to Transactions into a Cash Book. There is no
    content validation or error handling, expecting that the user
    provides the right file with the right content. Temporary solution
    to allow us to use the system right now
    """
    cash_book = CashBook.objects.get(slug=request.POST["cash_book"])

    import_transactions(request.FILES["ofx"], cash_book, request.user)

    return HttpResponseRedirect(
        reverse("bookkeeping:cash-book-transactions", args=(cash_book.slug,))
    )
