import csv

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from thebook.bookkeeping.models import CashBook


def _get_cash_book_transactions_context(cash_book):
    transactions = cash_book.transaction_set.all()
    return {
        "cash_book": cash_book,
        "transactions": transactions,
    }


def cash_book_transactions(request, cash_book_slug):
    cash_book = get_object_or_404(CashBook, slug=cash_book_slug)

    return render(
        request,
        "bookkeeping/transactions.html",
        context=_get_cash_book_transactions_context(cash_book),
    )


def cash_book_transactions_export_csv(request, cash_book_slug):
    cash_book = get_object_or_404(CashBook, slug=cash_book_slug)
    context = _get_cash_book_transactions_context(cash_book)

    output_filename = f"{cash_book_slug}-transactions.csv"
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
            "has_documents",
        ]
    )
    for transaction in context["transactions"]:
        writer.writerow(
            [
                transaction.id,
                transaction.reference,
                transaction.date,
                transaction.description,
                transaction.amount,
                transaction.notes,
                transaction.category.name,
                transaction.has_documents,
            ]
        )

    return response
