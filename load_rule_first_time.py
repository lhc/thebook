import re
from dataclasses import dataclass
from decimal import Decimal

from thebook.bookkeeping.models import Category, CategoryMatchRule


@dataclass()
class MatchRule:
    pattern: str
    category: "Category"
    value: Decimal = None
    comparison_function: str = None
    tags: list[str] = None


def create_first_set_of_matching_rules():
    donation, _ = Category.objects.get_or_create(name="Doação")
    bank_fees, _ = Category.objects.get_or_create(name="Tarifas Bancárias")
    bank_income, _ = Category.objects.get_or_create(name="Investimentos")
    cash_book_transfer, _ = Category.objects.get_or_create(
        name="Transferência entre livros-caixa"
    )
    services, _ = Category.objects.get_or_create(name="Serviços")
    taxes, _ = Category.objects.get_or_create(name="Impostos")
    membership_fee, _ = Category.objects.get_or_create(name="Contribuição Associativa")

    rules_to_add = [
        MatchRule(
            pattern="TARIFA BANCARIA Max Empresarial 1",
            category=bank_fees,
            tags=["banco", "recorrente"],
        ),
        MatchRule(
            pattern=".*CONTADORA.*",
            category=services,
            value=Decimal("-540"),
            comparison_function="EQ",
            tags=["contabilidade", "recorrente"],
        ),
        MatchRule(
            pattern="PAGTO ELETRON COBRANCA CONTADOR",
            category=services,
            value=Decimal("-207.80"),
            comparison_function="EQ",
            tags=["contabilidade", "recorrente"],
        ),
        MatchRule(
            pattern=".*ESTEVAN CASTILHO DE MACEDO.*",
            category=membership_fee,
            value=Decimal("85"),
            comparison_function="EQ",
            tags=["mensalidade"],
        ),
        MatchRule(
            pattern=".*ELITON P CRUVINEL.*",
            category=membership_fee,
            value=Decimal("85"),
            comparison_function="EQ",
            tags=["mensalidade"],
        ),
        MatchRule(
            pattern=".*RENNE SILVA G OLIVEIRA ROCHA.*",
            category=membership_fee,
            value=Decimal("85"),
            comparison_function="EQ",
            tags=["mensalidade"],
        ),
        MatchRule(
            pattern=".*Bruno Renatto Sugobon.*",
            category=membership_fee,
            value=Decimal("110"),
            comparison_function="EQ",
            tags=["mensalidade"],
        ),
        MatchRule(
            pattern=".*Mensalidade.*",
            category=membership_fee,
            value=Decimal("85"),
            comparison_function="EQ",
            tags=["mensalidade"],
        ),
        MatchRule(
            pattern=".*Mensalidade.*",
            category=membership_fee,
            value=Decimal("110"),
            comparison_function="EQ",
            tags=["mensalidade"],
        ),
        MatchRule(pattern="TARIFA BANCARIA", category=bank_fees, tags=["banco"]),
        MatchRule(
            pattern="CONTA DE TELEFONE", category=services, tags=["vivo", "recorrente"]
        ),
        MatchRule(
            pattern="CONTA DE AGUA", category=services, tags=["sanasa", "recorrente"]
        ),
        MatchRule(
            pattern="CONTA DE LUZ", category=services, tags=["cpfl", "recorrente"]
        ),
        MatchRule(
            pattern="COBRANCA ALUGUEL",
            category=services,
            tags=["aluguel", "recorrente"],
        ),
        MatchRule(pattern="RENTAB.INVEST FACILCRED", category=bank_income),
        MatchRule(
            pattern="SYSTEN CONSULTORIA", category=services, tags=["contabilidade"]
        ),
        MatchRule(pattern=".*CONTADOR.*", category=services, tags=["contabilidade"]),
        MatchRule(pattern="PAYPAL DO BRASIL", category=cash_book_transfer),
        MatchRule(
            pattern="PAGTO ELETRONICO TRIBUTO INTERNET --P.M CAMPINAS/SP",
            category=taxes,
        ),
        MatchRule(pattern="PAGAMENTO DA FATURA", category=cash_book_transfer),
    ]

    priority = 100
    for rule in rules_to_add:
        if not rule.tags:
            tags = []
        else:
            tags = rule.tags

        CategoryMatchRule.objects.create(
            priority=priority,
            pattern=rule.pattern,
            category=rule.category,
            value=rule.value,
            comparison_function=rule.comparison_function,
            tags=",".join(tags),
        )
        priority += 100
