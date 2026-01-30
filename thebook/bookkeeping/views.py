import csv
import datetime

from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _

from thebook.bookkeeping.importers import ImportTransactionsError, import_transactions
from thebook.bookkeeping.models import BankAccount, Document, Transaction


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
            "tags",
        ]
    )

    for transaction in context["transactions"]:
        transaction_tags = ",".join(tag.name for tag in transaction.tags.all())
        writer.writerow(
            [
                transaction.id,
                transaction.reference,
                transaction.date,
                transaction.description,
                transaction.amount,
                transaction.notes,
                transaction.category.name if transaction.category is not None else "",
                transaction.has_documents,
                transaction_tags,
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

    transactions = cash_book.transaction_set.select_related(
        "category"
    ).prefetch_related("documents")
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
        "cash_book": cash_book.with_summary(year=year, month=month),
        "transactions": transactions.order_by("date"),
        "year": year,
        "month": month,
        "previous_period": previous_period,
        "next_period": next_period,
    }


def cash_book_transactions(request, cash_book_slug):
    cash_book = get_object_or_404(BankAccount, slug=cash_book_slug)
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


def cash_book_import_transactions(request, cash_book_slug):
    cash_book = get_object_or_404(BankAccount, slug=cash_book_slug)

    start_date = request.POST.get("start_date") or None
    if start_date is not None:
        start_date = datetime.datetime.strptime(start_date, "%d/%m/%Y").date()

    end_date = request.POST.get("end_date") or None
    if end_date is not None:
        end_date = datetime.datetime.strptime(start_date, "%d/%m/%Y").date()

    try:
        file_type = request.POST["file_type"]
        transactions_file = None
        if file_type == "ofx":
            transactions_file = request.FILES["ofx_file"]
        elif file_type == "csv":
            transactions_file = request.FILES["csv_file"]
        elif file_type == "csv_cora_credit_card":
            transactions_file = request.FILES["csv_cora_credit_card_file"]

        import_transactions(
            transactions_file, file_type, cash_book, request.user, start_date, end_date
        )
    except ImportTransactionsError as err:
        messages.add_message(request, messages.ERROR, str(err))

    return HttpResponseRedirect(request.POST["next_url"])


def transaction_upload_document(request):
    transaction = get_object_or_404(Transaction, id=request.POST["transaction_id"])

    document = Document.objects.create(
        transaction=transaction,
        document_file=request.FILES["transaction_document"],
        notes=request.POST["notes"],
    )
    messages.add_message(request, messages.SUCCESS, _("File successfully uploaded."))

    return HttpResponseRedirect(request.POST["next_url"])


def partial_transaction_details(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)

    return render(
        request,
        "bookkeeping/partial/transaction_details.html",
        context={"transaction": transaction},
    )


def partial_cash_books_dashboard(request):
    today = datetime.date.today()

    month = int(request.GET.get("month") or today.month)
    year = int(request.GET.get("year") or today.year)

    reference_date = datetime.date(year, month, 1)
    previous_month_reference_date = reference_date - datetime.timedelta(days=10)
    next_month_reference_date = reference_date + datetime.timedelta(days=40)

    cash_books_summary = BankAccount.objects.filter(active=True).summary(
        year=year, month=month
    )
    return render(
        request,
        "bookkeeping/partial/cash_books_dashboard.html",
        context={
            "cash_books_summary": cash_books_summary,
            "month": int(month),
            "next_month": next_month_reference_date.month,
            "next_year": next_month_reference_date.year,
            "previous_month": previous_month_reference_date.month,
            "previous_year": previous_month_reference_date.year,
            "year": int(year),
        },
    )
