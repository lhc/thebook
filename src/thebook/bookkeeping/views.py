import csv

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from thebook.bookkeeping.models import CashBook
from thebook.bookkeeping.ofx_import import (
    import_transactions as import_ofx_transactions,
)
from thebook.bookkeeping.paypal_import import (
    import_transactions as import_paypal_transactions,
)


def cash_books(request):
    return render(request, "bookkeeping/cashbooks.html")


def all_transactions(request):
    return HttpResponse("All transactions")


def cash_book_transactions(request, cash_book_slug):
    cash_book = CashBook.objects.get(slug=cash_book_slug)
    year = request.GET.get("year") or None
    month = request.GET.get("month") or None

    query_string = ""
    if month is not None and year is not None:
        query_string = f"?year={year}&month={month}"

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
            "query_string": query_string,
            "transactions": transactions.with_cumulative_sum(),
        },
    )


def export_transactions(request, cash_book_slug):
    cash_book = CashBook.objects.get(slug=cash_book_slug)
    year = request.GET.get("year") or None
    month = request.GET.get("month") or None

    output_filename = f"{cash_book_slug}-transactions.csv"

    transactions = cash_book.transaction_set.all().select_related("category")
    if month is not None and year is not None:
        transactions = transactions.for_period(month, year)
        output_filename = f"{year}-{month}-{cash_book_slug}-transactions.csv"

    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{output_filename}"'},
    )

    writer = csv.writer(response)

    writer.writerow(
        [
            "id",
            "reference",
            "date",
            "description",
            "amount",
            "notes",
            "category",
        ]
    )
    for transaction in transactions:
        writer.writerow(
            [
                transaction.id,
                transaction.reference,
                transaction.date,
                transaction.description,
                transaction.amount,
                transaction.notes,
                transaction.category.name,
            ]
        )

    return response


def import_ofx(request):
    """
    This is a temporary view that imports the content of a OFX file
    and converts it to Transactions into a Cash Book. There is no
    content validation or error handling, expecting that the user
    provides the right file with the right content. Temporary solution
    to allow us to use the system right now
    """
    cash_book = CashBook.objects.get(slug=request.POST["cash_book"])

    import_ofx_transactions(request.FILES["ofx"], cash_book, request.user)

    return HttpResponseRedirect(
        reverse("bookkeeping:cash-book-transactions", args=(cash_book.slug,))
    )


def import_paypal_csv(request):
    """
    This is a temporary view that imports the content of a PayPal CSV
    and converts it to Transactions into a Cash Book. There is no
    content validation or error handling, expecting that the user
    provides the right file with the right content. Temporary solution
    to allow us to use the system right now
    """
    cash_book = CashBook.objects.get(slug=request.POST["cash_book"])

    import_paypal_transactions(request.FILES["csv"], cash_book, request.user)

    return HttpResponseRedirect(
        reverse("bookkeeping:cash-book-transactions", args=(cash_book.slug,))
    )
