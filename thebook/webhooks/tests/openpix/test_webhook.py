from http import HTTPStatus

import pytest

from django.test import Client
from django.urls import reverse


def test_webhook_reachable(client):
    response = client.post(
        reverse("webhooks:openpix-webhook"),
        headers={
            "X-OpenPix-Signature": "openpix-signature-value",
            "X-TheBook-Token": "thebook-token",
        },
    )

    assert response.status_code == HTTPStatus.OK


def test_webhook_does_not_have_csrf_protection():
    csrf_client = Client(enforce_csrf_checks=True)

    response = csrf_client.post(
        reverse("webhooks:openpix-webhook"),
        headers={
            "X-OpenPix-Signature": "openpix-signature-value",
            "X-TheBook-Token": "thebook-token",
        },
    )

    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    ["invalid_method"],
    [
        ("get",),
        ("head",),
        ("options",),
        ("put",),
        ("patch",),
        ("delete",),
        ("trace",),
    ],
)
def test_webhook_not_reachable_with_invalid_http_method(client, invalid_method):
    caller = getattr(client, invalid_method)
    response = caller(reverse("webhooks:openpix-webhook"))

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


def test_not_found_if_openpix_signature_missing(client):
    response = client.post(
        reverse("webhooks:openpix-webhook"),
        headers={
            "X-TheBook-Token": "thebook-token",
        },
    )

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_not_found_if_thebook_token_missing(client):
    response = client.post(
        reverse("webhooks:openpix-webhook"),
        headers={
            "X-OpenPix-Signature": "openpix-signature-value",
        },
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
