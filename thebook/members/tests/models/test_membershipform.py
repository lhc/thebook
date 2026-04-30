import datetime

import pytest
from freezegun import freeze_time

from django.core import mail

from thebook.members.models import MembershipForm


def test_when_created_valid_until_set_to_30_days_from_today(db):
    membership_form = MembershipForm(email="new_member@example.com")

    membership_form.save()
    membership_form.refresh_from_db()

    assert membership_form.valid_until == datetime.date.today() + datetime.timedelta(
        days=30
    )


@pytest.mark.parametrize(
    "current_date,is_still_valid",
    [
        (datetime.date(2026, 5, 15), True),
        (datetime.date(2026, 5, 30), True),
        (datetime.date(2026, 5, 31), False),
    ],
)
def test_check_if_membership_form_is_still_valid(db, current_date, is_still_valid):
    membership_form = MembershipForm(
        email="new_member@example.com",
        valid_until=datetime.date(2026, 5, 30),
    )
    membership_form.save()
    membership_form.refresh_from_db()

    with freeze_time(current_date):
        assert membership_form.is_still_valid is is_still_valid


def test_when_created_send_an_email_with_membership_instruction(db):
    membership_form = MembershipForm(
        email="new_member@example.com",
        valid_until=datetime.date(2026, 5, 30),
    )
    membership_form.save()

    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == "[thebook] Cadastro de pessoa associada ao LHC"
    mail.outbox[0].to == ["new_member@example.com"]
