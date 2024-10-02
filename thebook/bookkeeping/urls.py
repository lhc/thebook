from django.urls import path

from thebook.bookkeeping import views

app_name = "bookkeeping"

urlpatterns = [
    path(
        "cb/<slug:cash_book_slug>/transactions",
        views.cash_book_transactions,
        name="cash-book-transactions",
    ),
    path(
        "cb/<slug:cash_book_slug>/transactions/csv",
        views.cash_book_transactions_export_csv,
        name="cash-book-transactions-export-csv",
    ),
]
