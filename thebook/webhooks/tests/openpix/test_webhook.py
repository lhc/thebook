import json
from http import HTTPStatus

import pytest

from django.test import Client
from django.urls import reverse

from thebook.webhooks.models import OpenPixWebhookPayload


def test_webhook_reachable(db, client):
    response = client.post(
        reverse("webhooks:openpix-webhook"),
        headers={
            "X-OpenPix-Signature": "openpix-signature-value",
            "X-TheBook-Token": "thebook-token",
        },
    )

    assert response.status_code == HTTPStatus.OK


def test_webhook_does_not_have_csrf_protection(db):
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


def test_when_received_store_body_and_headers(db, client):
    thebook_token = "thebook-token"
    webhook_payload = {"event": "OPENPIX:TRANSACTION_RECEIVED"}

    response = client.post(
        reverse("webhooks:openpix-webhook"),
        webhook_payload,
        headers={
            "X-OpenPix-Signature": "openpix-signature-value",
            "X-TheBook-Token": thebook_token,
        },
        content_type="application/json",
    )

    assert OpenPixWebhookPayload.objects.filter(
        thebook_token=thebook_token, payload=json.dumps(webhook_payload)
    ).exists()
