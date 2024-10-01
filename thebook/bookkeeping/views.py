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
