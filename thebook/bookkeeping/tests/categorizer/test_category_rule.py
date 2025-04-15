import pytest
from model_bakery import baker

from thebook.bookkeeping.categorizer import CategoryRule
from thebook.bookkeeping.models import Category, Transaction


@pytest.fixture
def bank_fee_category():
    return Category(name="Bank Fee")


def test_rule_with_tag_can_not_be_applied_if_transaction_not_persisted(
    bank_fee_category,
):
    category_rule = CategoryRule(
        pattern="bank fee", category=bank_fee_category, tags=["bank"]
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


@pytest.mark.parametrize(
    "pattern,description,tags",
    [
        (r"\d{5} bank", "12345 bank", ["bank", "fees"]),
        (r"\d{5} bank", "12345 bank", ["bank"]),
        (r"\d{5} bank", "12345 bank", []),
    ],
)
def test_apply_tags_to_matched_transactions(
    db, bank_fee_category, pattern, description, tags
):
    category_rule = CategoryRule(
        pattern=pattern,
        category=bank_fee_category,
        tags=tags,
    )
    transaction = baker.make(Transaction, description=description)

    transaction, applied = category_rule.apply_rule(transaction)

    assert applied
    assert sorted(list(transaction.tags.names())) == sorted(tags)
