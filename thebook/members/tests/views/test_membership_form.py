import datetime
import uuid
from http import HTTPStatus

import pytest
from freezegun import freeze_time

from django.core import mail
from django.urls import reverse

from thebook.members.models import MembershipForm


@pytest.mark.freeze_time("2026-05-04")
def test_ok_with_valid_identifier_not_expired_and_not_processed(client, db):
    membership_form = MembershipForm.objects.create(
        uuid=uuid.uuid4(),
        email="person@example.com",
        valid_until=datetime.date(2026, 6, 3),
        processed=False,
    )

    membership_form_url = reverse(
        "members:membership-form", kwargs={"membership_form_uuid": membership_form.uuid}
    )

    response = client.get(membership_form_url)

    assert response.status_code == HTTPStatus.OK


@pytest.mark.freeze_time("2026-05-04")
def test_not_found_with_invalid_identifier(client, db):
    membership_form = MembershipForm.objects.create(
        uuid=uuid.uuid4(),
        email="person@example.com",
        valid_until=datetime.date(2026, 6, 3),
        processed=False,
    )

    membership_form_url = reverse(
        "members:membership-form", kwargs={"membership_form_uuid": uuid.uuid4()}
    )

    response = client.get(membership_form_url)

    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.freeze_time("2026-06-04")
def test_not_found_if_expired(client, db):
    membership_form = MembershipForm.objects.create(
        uuid=uuid.uuid4(),
        email="person@example.com",
        valid_until=datetime.date(2026, 6, 3),
        processed=False,
    )

    membership_form_url = reverse(
        "members:membership-form", kwargs={"membership_form_uuid": membership_form.uuid}
    )

    response = client.get(membership_form_url)

    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.freeze_time("2026-05-04")
def test_not_found_if_already_processed(client, db):
    membership_form = MembershipForm.objects.create(
        uuid=uuid.uuid4(),
        email="person@example.com",
        valid_until=datetime.date(2026, 6, 3),
        processed=True,
    )

    membership_form_url = reverse(
        "members:membership-form", kwargs={"membership_form_uuid": membership_form.uuid}
    )

    response = client.get(membership_form_url)

    assert response.status_code == HTTPStatus.NOT_FOUND
