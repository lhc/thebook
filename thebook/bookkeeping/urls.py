from django.urls import path

from thebook.bookkeeping import views

app_name = "bookkeeping"

urlpatterns = [
    path(
        "bank_account/<slug:bank_account_slug>",
        views.BankAccountView.as_view(),
        name="bank-account",
    ),
    path(
        "cb/<slug:bank_account_slug>/transactions",
        views.bank_account_transactions,
        name="bank-account-transactions",
    ),
    path(
        "cb/<slug:bank_account_slug>/transactions/import",
        views.bank_account_import_transactions,
        name="bank-account-import-transactions",
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
    path(
        "partial/cb/dashboard",
        views.partial_bank_accounts_dashboard,
        name="partial-bank-accounts-dashboard",
    ),
]
