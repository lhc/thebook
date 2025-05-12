import re
from dataclasses import dataclass
from decimal import Decimal


@dataclass()
class CategoryRule:
    pattern: str
    category: "Category"
    value: Decimal = None
    comparison_function: str = None
    tags: list[str] = None

    def apply_rule(self, transaction):
        applied = False
        if self.tags and not transaction.id:
            raise ValueError(
                "You need to save the transaction before adding tags to it."
            )

        string_pattern_matched = bool(
            re.match(self.pattern, transaction.description, re.IGNORECASE)
        )

        if self.value:
            value_matched = False
            if self.comparison_function == "EQ" and transaction.amount == self.value:
                value_matched = True
            elif self.comparison_function == "LTE" and transaction.amount <= self.value:
                value_matched = True
            elif self.comparison_function == "GTE" and transaction.amount >= self.value:
                value_matched = True
        else:
            value_matched = True

        applied = all(
            [
                string_pattern_matched,
                value_matched,
            ]
        )
        if applied:
            transaction.category = self.category
            if self.tags:
                transaction.tags.add(*self.tags)
            transaction.save()

        return transaction, applied


def get_categorize_rules():
    from thebook.bookkeeping.models import Category

    donation, _ = Category.objects.get_or_create(name="Doação")
    bank_fees, _ = Category.objects.get_or_create(name="Tarifas Bancárias")
    bank_income, _ = Category.objects.get_or_create(name="Investimentos")
    cash_book_transfer, _ = Category.objects.get_or_create(
        name="Transferência entre contas"
    )
    services, _ = Category.objects.get_or_create(name="Serviços")
    taxes, _ = Category.objects.get_or_create(name="Impostos")
    membership_fee, _ = Category.objects.get_or_create(name="Contribuição Associativa")

    return [
        CategoryRule(
            pattern="TARIFA BANCARIA Max Empresarial 1",
            category=bank_fees,
            tags=["banco", "recorrente"],
        ),
        CategoryRule(
            pattern=".*CONTADORA.*",
            category=services,
            value=Decimal("-540"),
            comparison_function="EQ",
            tags=["contabilidade", "recorrente"],
        ),
        CategoryRule(
            pattern="PAGTO ELETRON COBRANCA CONTADOR",
            category=services,
            value=Decimal("-207.80"),
            comparison_function="EQ",
            tags=["contabilidade", "recorrente"],
        ),
        CategoryRule(
            pattern=".*ESTEVAN CASTILHO DE MACEDO.*",
            category=membership_fee,
            value=Decimal("85"),
            comparison_function="EQ",
            tags=["mensalidade"],
        ),
        CategoryRule(
            pattern=".*ELITON P CRUVINEL.*",
            category=membership_fee,
            value=Decimal("85"),
            comparison_function="EQ",
            tags=["mensalidade"],
        ),
        CategoryRule(
            pattern=".*RENNE SILVA G OLIVEIRA ROCHA.*",
            category=membership_fee,
            value=Decimal("85"),
            comparison_function="EQ",
            tags=["mensalidade"],
        ),
        CategoryRule(
            pattern=".*Bruno Renatto Sugobon.*",
            category=membership_fee,
            value=Decimal("110"),
            comparison_function="EQ",
            tags=["mensalidade"],
        ),
        CategoryRule(
            pattern=".*Mensalidade.*",
            category=membership_fee,
            value=Decimal("85"),
            comparison_function="EQ",
            tags=["mensalidade"],
        ),
        CategoryRule(
            pattern=".*Mensalidade.*",
            category=membership_fee,
            value=Decimal("110"),
            comparison_function="EQ",
            tags=["mensalidade"],
        ),
        CategoryRule(pattern="TARIFA BANCARIA", category=bank_fees),
        CategoryRule(
            pattern="CONTA DE TELEFONE", category=services, tags=["vivo", "recorrente"]
        ),
        CategoryRule(
            pattern="CONTA DE AGUA", category=services, tags=["sanasa", "recorrente"]
        ),
        CategoryRule(
            pattern="CONTA DE LUZ", category=services, tags=["cpfl", "recorrente"]
        ),
        CategoryRule(
            pattern="COBRANCA ALUGUEL",
            category=services,
            tags=["aluguel", "recorrente"],
        ),
        CategoryRule(pattern="RENTAB.INVEST FACILCRED", category=bank_income),
        CategoryRule(
            pattern="SYSTEN CONSULTORIA", category=services, tags=["contabilidade"]
        ),
        CategoryRule(pattern=".*CONTADOR.*", category=services, tags=["contabilidade"]),
        CategoryRule(pattern="PAYPAL DO BRASIL", category=cash_book_transfer),
        CategoryRule(
            pattern="PAGTO ELETRONICO TRIBUTO INTERNET --P.M CAMPINAS/SP",
            category=taxes,
        ),
        CategoryRule(pattern="PAGAMENTO DA FATURA", category=cash_book_transfer),
    ]
