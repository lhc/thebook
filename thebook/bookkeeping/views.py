import calendar
import csv
import datetime

from django.contrib import messages
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from django.views import View

from thebook.bookkeeping.importers import ImportTransactionsError, import_transactions
from thebook.bookkeeping.models import BankAccount, Document, Transaction


def _csv_bank_account_transactions(context):
    bank_account = context["bank_account"]
    output_filename = f"{bank_account.slug}-transactions.csv"
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


def _get_bank_account_transactions_context(bank_account, *, year=None, month=None):
    previous_period, next_period = None, None

    if year is not None:
        year = int(year)
    if month is not None:
        month = int(month)

    transactions = bank_account.transactions.select_related(
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
        "bank_account": bank_account.with_summary(year=year, month=month),
        "transactions": transactions.order_by("date"),
        "year": year,
        "month": month,
        "previous_period": previous_period,
        "next_period": next_period,
    }


def bank_account_transactions(request, bank_account_slug):
    bank_account = get_object_or_404(BankAccount, slug=bank_account_slug)
    response_context = _get_bank_account_transactions_context(
        bank_account, year=request.GET.get("year"), month=request.GET.get("month")
    )

    response_format = request.GET.get("format")
    if response_format == "csv":
        return _csv_bank_account_transactions(response_context)

    return render(
        request,
        "bookkeeping/transactions.html",
        context=response_context,
    )


def bank_account_import_transactions(request, bank_account_slug):
    bank_account = get_object_or_404(BankAccount, slug=bank_account_slug)

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
            transactions_file,
            file_type,
            bank_account,
            request.user,
            start_date,
            end_date,
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


def partial_bank_accounts_dashboard(request):
    today = datetime.date.today()

    month = int(request.GET.get("month") or today.month)
    year = int(request.GET.get("year") or today.year)

    reference_date = datetime.date(year, month, 1)
    previous_month_reference_date = reference_date - datetime.timedelta(days=10)
    next_month_reference_date = reference_date + datetime.timedelta(days=40)

    bank_accounts_summary = BankAccount.objects.filter(active=True).summary(
        year=year, month=month
    )
    return render(
        request,
        "bookkeeping/partial/bank_accounts_dashboard.html",
        context={
            "bank_accounts_summary": bank_accounts_summary,
            "month": int(month),
            "next_month": next_month_reference_date.month,
            "next_year": next_month_reference_date.year,
            "previous_month": previous_month_reference_date.month,
            "previous_year": previous_month_reference_date.year,
            "year": int(year),
        },
    )


def _get_date_range_from_request_query_strings(request):
    """Return start and end date based on the provided query string of the request

    If not provided, or partially provided, it must return the current month date range.
    """
    start_date = request.GET.get("start_date") or ""
    end_date = request.GET.get("end_date") or ""

    try:
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        start_date, end_date = None, None

    if start_date is None or end_date is None:
        today = datetime.date.today()
        current_month = today.month
        current_year = today.year

        start_date = datetime.date(current_year, current_month, 1)

        _, last_day_of_month = calendar.monthrange(current_year, current_month)
        end_date = datetime.date(
            current_year, current_month, last_day_of_month
        ) + datetime.timedelta(days=1)

    return start_date, end_date


class BankAccountView(View):
    def get(self, request, bank_account_slug):
        start_date, end_date = _get_date_range_from_request_query_strings(request)

        bank_account = get_object_or_404(
            BankAccount.objects.with_summary(start_date=start_date, end_date=end_date),
            slug=bank_account_slug,
        )

        transactions = (
            bank_account.transactions.within_period(
                start_date=start_date, end_date=end_date
            )
            .select_related("category")
            .prefetch_related("documents")
        )

        return render(
            request,
            "bookkeeping/bank_account.html",
            context={
                "bank_account": bank_account,
                "end_date": end_date,
                "start_date": start_date,
                "transactions": transactions,
            },
        )


class ReportCashBookView(View):

    def get(self, request):
        start_date, end_date = _get_date_range_from_request_query_strings(request)

        opening_balance = Transaction.objects.filter(date__lt=start_date).aggregate(
            Sum("amount", default=0)
        )["amount__sum"]
        transactions = Transaction.objects.within_period(
            start_date=start_date, end_date=end_date
        ).with_info_for_cash_book()

        return render(
            request,
            "bookkeeping/reports/cash_book.html",
            context={
                "end_date": end_date,
                "opening_balance": opening_balance,
                "start_date": start_date,
                "transactions": transactions,
            },
        )
