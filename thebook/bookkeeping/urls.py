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
        "cb/<slug:cash_book_slug>/transactions/import",
        views.cash_book_import_transactions,
        name="cash-book-import-transactions",
    ),
    path(
        "transaction/upload",
        views.transaction_upload_document,
        name="transaction-upload-document",
    ),
    path(
        "partial/transaction/<int:transaction_id>",
        views.partial_transaction_details,
        name="partial-transaction-details",
    ),
]
