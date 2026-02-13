from decimal import Decimal

import pytest
from model_bakery import baker

from thebook.bookkeeping.models import Category, CategoryMatchRule, Transaction


@pytest.fixture
def bank_fee_category(db):
    return Category.objects.create(name="Bank Fee")


def test_can_not_apply_rule_in_not_persisted_transaction(
    bank_fee_category,
):
    category_rule = CategoryMatchRule.objects.create(
        pattern="bank fee", category=bank_fee_category, tags="bank"
    )
    transaction = baker.prepare(Transaction, description="bank fee")
    with pytest.raises(ValueError):
        transaction, applied = category_rule.apply_rule(transaction)


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
def test_apply_rule_by_regex_pattern(db, bank_fee_category, pattern, description):
    category_rule = CategoryMatchRule.objects.create(
        pattern=pattern,
        category=bank_fee_category,
    )
    transaction = baker.make(Transaction, description=description)

    transaction, applied = category_rule.apply_rule(transaction)

    assert applied

    transaction.refresh_from_db()
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
    db, bank_fee_category, pattern, description
):
    category_rule = CategoryMatchRule.objects.create(
        pattern=pattern,
        category=bank_fee_category,
    )
    transaction = baker.make(Transaction, description=description)

    transaction, applied = category_rule.apply_rule(transaction)

    assert not applied

    transaction.refresh_from_db()
    assert transaction.category is None


@pytest.mark.parametrize(
    "pattern,description,tags",
    [
        (r"\d{5} bank", "12345 bank", "bank,fees"),
        (r"\d{5} bank", "12345 bank", "bank"),
    ],
)
def test_apply_tags_to_matched_transactions(
    db, bank_fee_category, pattern, description, tags
):
    category_rule = CategoryMatchRule.objects.create(
        pattern=pattern,
        category=bank_fee_category,
        tags=tags,
    )
    transaction = baker.make(Transaction, description=description)

    transaction, applied = category_rule.apply_rule(transaction)

    assert applied

    transaction.refresh_from_db()
    assert sorted(list(transaction.tags.names())) == sorted(tags.split(","))


@pytest.mark.parametrize(
    "rule_value,comparison_function,amount,expected_applied",
    [
        (Decimal("10.00"), "EQ", Decimal("10.00"), True),
        (Decimal("10.00"), "LTE", Decimal("10.00"), True),
        (Decimal("10.00"), "GTE", Decimal("10.00"), True),
        (Decimal("10.00"), "EQ", Decimal("9.00"), False),
        (Decimal("10.00"), "LTE", Decimal("11.00"), False),
        (Decimal("10.00"), "GTE", Decimal("8.50"), False),
        (Decimal("10.00"), "NEQ", Decimal("10.00"), False),
        (Decimal("10.00"), "NEQ", Decimal("9.00"), True),
    ],
)
def test_apply_rule_considering_value(
    db,
    bank_fee_category,
    rule_value,
    comparison_function,
    amount,
    expected_applied,
):
    category_rule = CategoryMatchRule.objects.create(
        pattern="bank fee",
        category=bank_fee_category,
        value=rule_value,
        comparison_function=comparison_function,
    )
    transaction = baker.make(Transaction, description="bank fee", amount=amount)

    transaction, applied = category_rule.apply_rule(transaction)

    assert applied == expected_applied
