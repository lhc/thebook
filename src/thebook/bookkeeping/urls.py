from django.urls import path

from thebook.bookkeeping import views

app_name = "bookkeeping"

urlpatterns = [
    path("all/transactions", views.all_transactions, name="all-transactions"),
    path("cb/", views.cash_books, name="cash-books"),
    path(
        "cb/<slug:cash_book_slug>/transactions",
        views.cash_book_transactions,
        name="cash-book-transactions",
    ),
    path(
        "cb/<slug:cash_book_slug>/transactions/export",
        views.export_transactions,
        name="export-transactions",
    ),
    path("cb/import-ofx", views.import_ofx, name="import-ofx"),
    path("cb/import-paypal-csv", views.import_paypal_csv, name="import-paypal-csv"),
]
