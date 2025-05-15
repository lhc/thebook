from decimal import Decimal

import pytest

from django.db.utils import IntegrityError

from thebook.bookkeeping.models import Category, CategoryMatchRule


@pytest.fixture
def category():
    return Category.objects.create(name="Test Category")


def test_priority_must_be_unique(db, category):
    _ = CategoryMatchRule.objects.create(
        priority=100, pattern="test_pattern", category=category
    )
    with pytest.raises(IntegrityError):
        CategoryMatchRule.objects.create(
            priority=100, pattern="another_pattern", category=category
        )


def test_when_value_is_provided_comparison_function_is_also_required(db, category):
    with pytest.raises(IntegrityError):
        _ = CategoryMatchRule.objects.create(
            priority=100, pattern="pattern", category=category, value=Decimal("42.0")
        )


def test_when_comparison_function_is_provided_value_is_also_required(db, category):
    with pytest.raises(IntegrityError):
        _ = CategoryMatchRule.objects.create(
            priority=100,
            pattern="pattern",
            category=category,
            comparison_function="EQ",
        )


def test_valid_when_comparison_function_and_value_are_provided(db, category):
    try:
        category_match_rule = CategoryMatchRule.objects.create(
            priority=100,
            pattern="pattern",
            category=category,
            value=Decimal("42.0"),
            comparison_function="EQ",
        )
    except IntegrityError:
        pytest.fail("It should validate")


@pytest.mark.parametrize(
    "comparison_function",
    [
        "EQ",
        "LTE",
        "GTE",
    ],
)
def test_comparison_function_must_be_a_valid_value(db, category, comparison_function):
    try:
        category_match_rule = CategoryMatchRule.objects.create(
            priority=100,
            pattern="pattern",
            category=category,
            value=Decimal("42.0"),
            comparison_function=comparison_function,
        )
    except IntegrityError:
        pytest.fail("It should validate")


def test_fail_when_comparison_function_is_not_a_valid_value(db, category):
    with pytest.raises(IntegrityError):
        _ = CategoryMatchRule.objects.create(
            priority=100,
            pattern="pattern",
            category=category,
            value=Decimal("42.0"),
            comparison_function="XXX",
        )
