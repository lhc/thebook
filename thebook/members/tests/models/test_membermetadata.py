from decimal import Decimal

import pytest
from model_bakery import baker

from thebook.bookkeeping.models import Category, CategoryMatchRule
from thebook.members.models import (
    Member,
    MemberMetadata,
    MemberMetadataKeys,
    Membership,
)


@pytest.fixture
def membership_fee_category(db, scope="module"):
    category, _ = Category.objects.get_or_create(name="Contribuição Associativa")
    return category


def test_when_paypal_payer_id_is_set_for_member_create_category_matching_rule(
    db, membership_fee_category
):
    member = baker.make(Member)
    membership = baker.make(
        Membership, member=member, membership_fee_amount=Decimal("42.12")
    )

    paypal_payer_id = "Q64J6VDR3DBHN"

    MemberMetadata.objects.create(
        member=member,
        key=MemberMetadataKeys.PAYPAL_PAYER_ID,
        value=paypal_payer_id,
    )

    assert CategoryMatchRule.objects.filter(
        pattern=f".*{paypal_payer_id}.*",
        category=membership_fee_category,
        value=membership.membership_fee_amount,
        comparison_function="EQ",
    ).exists()
