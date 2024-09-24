from django.conf import settings

from thebook.bookkeeping.models import Category, Transaction

DONATION = "Doação"
RECURRING_DONATION = "Doação Recorrente"
BANK_FEES = "Tarifas Bancárias"
BANK_INCOME = "Investimentos"
RECURRING = "Recorrente"
MEMBERSHIP_FEE = "Mensalidades"
CASH_BOOK_TRANSFER = "Transferência entre contas"
ACCOUNTANT = "Contabilidade"


def categorize():
    uncategorized, _ = Category.objects.get_or_create(
        name=settings.BOOKKEEPING_UNCATEGORIZED
    )
    donation, _ = Category.objects.get_or_create(name=DONATION)
    recurring_donation, _ = Category.objects.get_or_create(name=RECURRING_DONATION)
    bank_fees, _ = Category.objects.get_or_create(name=BANK_FEES)
    bank_income, _ = Category.objects.get_or_create(name=BANK_INCOME)
    recurring, _ = Category.objects.get_or_create(name=RECURRING)
    cash_book_transfer, _ = Category.objects.get_or_create(name=CASH_BOOK_TRANSFER)
    accountant, _ = Category.objects.get_or_create(name=ACCOUNTANT)

    for transaction in Transaction.objects.filter(category=uncategorized):
        if "TARIFA BANCARIA" in transaction.description:
            transaction.category = bank_fees
        elif "CONTA DE TELEFONE" in transaction.description:
            transaction.category = recurring
        elif "CONTA DE AGUA" in transaction.description:
            transaction.category = recurring
        elif "CONTA DE LUZ" in transaction.description:
            transaction.category = recurring
        elif "COBRANCA ALUGUEL" in transaction.description:
            transaction.category = recurring
        elif "RENTAB.INVEST FACILCRED" in transaction.description:
            transaction.category = bank_income
        elif "SYSTEN CONSULTORIA" in transaction.description:
            transaction.category = accountant
        elif "CONTADOR" in transaction.description:
            transaction.category = accountant
        elif (
            "TED-TRANSF ELET DISPON REMET.PAYPAL DO BRASIL SER"
            in transaction.description
        ):
            transaction.category = cash_book_transfer
        elif 0 < transaction.amount < 50:
            transaction.category = donation

        transaction.save()
