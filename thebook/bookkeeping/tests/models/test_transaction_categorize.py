import pytest

from model_bakery import baker
from thebook.bookkeeping.models import Category, Transaction


@pytest.fixture
def accountant():
    return Category.objects.create(name="Contabilidade")


@pytest.fixture
def bank_fees():
    return Category.objects.create(name="Tarifas Bancárias")


@pytest.fixture
def recurring():
    return Category.objects.create(name="Recorrente")


@pytest.fixture
def uncategorized():
    return Category.objects.create(name="Uncategorized")


@pytest.fixture
def expected_category(request, accountant, bank_fees, recurring, uncategorized):
    return {
        "accountant": accountant,
        "bank_fees": bank_fees,
        "recurring": recurring,
        "uncategorized": uncategorized,
    }.get(request.param)


@pytest.fixture
def category_description_rules(accountant, bank_fees, recurring):
    return {
        "TARIFA BANCARIA": bank_fees,
        "CONTA DE TELEFONE": recurring,
        "CONTADOR": accountant,
    }


@pytest.mark.parametrize(
    "description,expected_category",
    [
        ("TARIFA BANCARIA Max Empresarial 1", "bank_fees"),
        ("tarifa bancaria max empresarial 1", "bank_fees"),
        ("CONTA DE TELEFONE VIVO FIXO-NAC 13 DIG-9520430", "recurring"),
        ("PAGTO ELETRON COBRANCA CONTADORA", "accountant"),
        ("PAGTO ELETRON COBRANCA CONTADOR", "accountant"),
    ],
    indirect=["expected_category"],
)
def test_set_transaction_category_following_description_rules(
    db, category_description_rules, uncategorized, description, expected_category
):
    transaction = baker.make(
        Transaction, description=description, category=uncategorized
    )

    transaction.categorize(category_description_rules)

    assert transaction.category == expected_category


def test_categorize_transaction_is_persisted(db, accountant, uncategorized):
    transaction = baker.make(Transaction, description="TEST", category=uncategorized)
    assert transaction.category == uncategorized

    transaction.categorize({"TEST": accountant})

    transaction.refresh_from_db()
    assert transaction.category == accountant


def test_categorize_transaction_dont_change_if_no_rule_match(db, accountant, bank_fees):
    transaction = baker.make(Transaction, description="TEST", category=bank_fees)

    transaction.categorize({"RULE": accountant})

    transaction.refresh_from_db()
    assert transaction.category == bank_fees


def test_default_categorize_rules_if_not_provided(db, mocker, bank_fees, uncategorized):
    test_rules = {
        "TARIFA BANCARIA": bank_fees,
    }
    mocker.patch(
        "thebook.bookkeeping.models.get_categorize_rules", return_value=test_rules
    )

    transaction = baker.make(
        Transaction, description="TARIFA BANCARIA", category=uncategorized
    )

    transaction.categorize()

    transaction.refresh_from_db()
    assert transaction.category == bank_fees
