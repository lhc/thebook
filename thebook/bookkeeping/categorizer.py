import re
from dataclasses import dataclass
from decimal import Decimal


@dataclass()
class CategoryMatchRule:
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
        CategoryMatchRule(
            pattern="TARIFA BANCARIA Max Empresarial 1",
            category=bank_fees,
            tags=["banco", "recorrente"],
        ),
        CategoryMatchRule(
            pattern=".*CONTADORA.*",
            category=services,
            value=Decimal("-540"),
            comparison_function="EQ",
            tags=["contabilidade", "recorrente"],
        ),
        CategoryMatchRule(
            pattern="PAGTO ELETRON COBRANCA CONTADOR",
            category=services,
            value=Decimal("-207.80"),
            comparison_function="EQ",
            tags=["contabilidade", "recorrente"],
        ),
        CategoryMatchRule(
            pattern=".*ESTEVAN CASTILHO DE MACEDO.*",
            category=membership_fee,
            value=Decimal("85"),
            comparison_function="EQ",
            tags=["mensalidade"],
        ),
        CategoryMatchRule(
            pattern=".*ELITON P CRUVINEL.*",
            category=membership_fee,
            value=Decimal("85"),
            comparison_function="EQ",
            tags=["mensalidade"],
        ),
        CategoryMatchRule(
            pattern=".*RENNE SILVA G OLIVEIRA ROCHA.*",
            category=membership_fee,
            value=Decimal("85"),
            comparison_function="EQ",
            tags=["mensalidade"],
        ),
        CategoryMatchRule(
            pattern=".*Bruno Renatto Sugobon.*",
            category=membership_fee,
            value=Decimal("110"),
            comparison_function="EQ",
            tags=["mensalidade"],
        ),
        CategoryMatchRule(
            pattern=".*Mensalidade.*",
            category=membership_fee,
            value=Decimal("85"),
            comparison_function="EQ",
            tags=["mensalidade"],
        ),
        CategoryMatchRule(
            pattern=".*Mensalidade.*",
            category=membership_fee,
            value=Decimal("110"),
            comparison_function="EQ",
            tags=["mensalidade"],
        ),
        CategoryMatchRule(pattern="TARIFA BANCARIA", category=bank_fees),
        CategoryMatchRule(
            pattern="CONTA DE TELEFONE", category=services, tags=["vivo", "recorrente"]
        ),
        CategoryMatchRule(
            pattern="CONTA DE AGUA", category=services, tags=["sanasa", "recorrente"]
        ),
        CategoryMatchRule(
            pattern="CONTA DE LUZ", category=services, tags=["cpfl", "recorrente"]
        ),
        CategoryMatchRule(
            pattern="COBRANCA ALUGUEL",
            category=services,
            tags=["aluguel", "recorrente"],
        ),
        CategoryMatchRule(pattern="RENTAB.INVEST FACILCRED", category=bank_income),
        CategoryMatchRule(
            pattern="SYSTEN CONSULTORIA", category=services, tags=["contabilidade"]
        ),
        CategoryMatchRule(pattern=".*CONTADOR.*", category=services, tags=["contabilidade"]),
        CategoryMatchRule(pattern="PAYPAL DO BRASIL", category=cash_book_transfer),
        CategoryMatchRule(
            pattern="PAGTO ELETRONICO TRIBUTO INTERNET --P.M CAMPINAS/SP",
            category=taxes,
        ),
        CategoryMatchRule(pattern="PAGAMENTO DA FATURA", category=cash_book_transfer),
    ]
