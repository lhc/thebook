from django.conf import settings

from thebook.bookkeeping.models import Category, Transaction

DONATION = "Doação"
RECURRING_DONATION = "Doação Recorrente"
BANK_FEES = "Tarifas Bancárias"
BANK_INCOME = "Investimentos"
RECURRING = "Recorrente"
MEMBERSHIP_FEE = "Mensalidade"
CASH_BOOK_TRANSFER = "Transferência entre contas"
ACCOUNTANT = "Contabilidade"
TAXES = "Impostos"


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
    taxes, _ = Category.objects.get_or_create(name=TAXES)
    membership_fee, _ = Category.objects.get_or_create(name=MEMBERSHIP_FEE)

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
        elif (
            "TED-TRANSF ELET DISPON REMET.PAYPAL DO BRASIL INS"
            in transaction.description
        ):
            transaction.category = cash_book_transfer
        elif "TRANSFERENCIA PIX REM: PAYPAL DO BRASIL INST" in transaction.description:
            transaction.category = cash_book_transfer
        elif (
            "Transferência recebida - Paypal Do Brasil Instituicao De Pagamento Ltda"
            in transaction.description
        ):
            transaction.category = cash_book_transfer
        elif (
            "Transf Pix recebida - PAYPAL DO BRASIL INSTITUICAO DE PAGAMENTO LTDA"
            in transaction.description
        ):
            transaction.category = cash_book_transfer
        elif (
            "PAGTO ELETRONICO TRIBUTO INTERNET --P.M CAMPINAS/SP"
            in transaction.description
        ):
            transaction.category = taxes
            transaction.notes = "ISSQN"
        elif (
            "TRANSFERENCIA PIX REM: ELITON P CRUVINEL" in transaction.description
            and transaction.amount == 75
        ):
            transaction.category = membership_fee
        elif (
            "TRANSFERENCIA PIX REM: ELITON P CRUVINEL" in transaction.description
            and transaction.amount == 85
        ):
            transaction.category = membership_fee
        elif (
            "TRANSFERENCIA PIX REM: ESTEVAN CASTILHO DE M" in transaction.description
            and transaction.amount == 85
        ):
            transaction.category = membership_fee
        elif 0 < transaction.amount < 50:
            transaction.category = donation

        transaction.save()
