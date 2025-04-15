import pytest
from model_bakery import baker

from thebook.bookkeeping.categorizer import CategoryRule
from thebook.bookkeeping.models import Category, Transaction


@pytest.fixture
def bank_fee_category():
    return Category(name="Bank Fee")


@pytest.fixture
def membership_fee_category():
    return Category(name="Membership Fee")


@pytest.mark.parametrize(
    "pattern,description",
    [
        (r"bank fee", "bank fee"),
        (r"bank fee", "BANK FEE"),
        (r"bank.*", "bank fee"),
        (r"bank.*", "BANK FEE"),
        (r"\d{5} bank", "12345 bank"),
    ],
)
def test_apply_rule_by_regex_pattern(bank_fee_category, pattern, description):
    category_rule = CategoryRule(
        pattern=pattern,
        category=bank_fee_category,
    )
    transaction = baker.prepare(Transaction, description=description)

    transaction, applied = category_rule.apply_rule(transaction)

    assert applied
    assert transaction.category == bank_fee_category


@pytest.mark.parametrize(
    "pattern,description",
    [
        (r"bank.*", "nubank"),
        (r"\d{6} bank", "12345 bank"),
        (r"bank.*", "Transfer to Guybrush"),
    ],
)
def test_do_not_apply_rule_when_regex_not_a_match(
    bank_fee_category, pattern, description
):
    category_rule = CategoryRule(
        pattern=pattern,
        category=bank_fee_category,
    )
    transaction = baker.prepare(Transaction, description=description)

    transaction, applied = category_rule.apply_rule(transaction)

    assert not applied
    assert transaction.category is None
