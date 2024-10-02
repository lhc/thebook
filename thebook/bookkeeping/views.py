import csv
import datetime

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from thebook.bookkeeping.models import CashBook


def _csv_cash_book_transactions(context):
    cash_book = context["cash_book"]
    output_filename = f"{cash_book.slug}-transactions.csv"
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


def _get_periods(year, month):
    if not year and not month:
        return None, None

    if year and not month:
        previous_period = f"year={year - 1}"
        next_period = f"year={year + 1}"
        return previous_period, next_period

    reference_date = datetime.date(year, month, 1)
    previous_date = reference_date - datetime.timedelta(days=1)
    next_date = reference_date + datetime.timedelta(days=31)
    next_date = datetime.date(next_date.year, next_date.month, 1)

    previous_period = f"year={previous_date.year}&month={previous_date.month}"
    next_period = f"year={next_date.year}&month={next_date.month}"

    return previous_period, next_period


def _get_cash_book_transactions_context(cash_book, *, year=None, month=None):
    previous_period, next_period = None, None

    if year is not None:
        year = int(year)
    if month is not None:
        month = int(month)

    transactions = cash_book.transaction_set.all()
    if year:
        transactions = transactions.filter(date__year=year)
        if month in range(1, 13):
            transactions = transactions.filter(date__month=month)
        else:
            month = None
    else:
        year = None
        month = None

    previous_period, next_period = _get_periods(year, month)

    return {
        "cash_book": cash_book,
        "transactions": transactions,
        "year": year,
        "month": month,
        "previous_period": previous_period,
        "next_period": next_period,
    }


def cash_book_transactions(request, cash_book_slug):
    cash_book = get_object_or_404(CashBook, slug=cash_book_slug)
    response_context = _get_cash_book_transactions_context(
        cash_book, year=request.GET.get("year"), month=request.GET.get("month")
    )

    response_format = request.GET.get("format")
    if response_format == "csv":
        return _csv_cash_book_transactions(response_context)

    return render(
        request,
        "bookkeeping/transactions.html",
        context=response_context,
    )
