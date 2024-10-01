from django.shortcuts import get_object_or_404, render

from thebook.bookkeeping.models import CashBook


# Create your views here.
def cash_book_transactions(request, cash_book_slug):
    cash_book = get_object_or_404(CashBook, slug=cash_book_slug)

    return render(
        request,
        "bookkeeping/transactions.html",
    )
