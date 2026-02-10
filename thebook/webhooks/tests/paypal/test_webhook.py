import json
from http import HTTPStatus

import pytest

from django.test import Client
from django.urls import reverse

from thebook.webhooks.models import PaypalWebhookPayload


@pytest.fixture
def required_headers():
    return {
        "Paypal-Transmission-Time": "paypal-transmission-time",
        "Paypal-Auth-Version": "paypal-auth-version",
        "Paypal-Cert-Url": "paypal-cert-url",
        "Paypal-Auth-Algo": "paypal-auth-algo",
        "Paypal-Transmission-Sig": "paypal-transmission-sig",
        "Paypal-Transmission-Id": "paypal-transmission-id",
        "Correlation-Id": "correlation-id",
    }


def test_webhook_reachable(db, client, required_headers):
    response = client.post(
        reverse("webhooks:paypal-webhook"),
        headers=required_headers,
    )

    assert response.status_code == HTTPStatus.OK


def test_webhook_does_not_have_csrf_protection(db, required_headers):
    csrf_client = Client(enforce_csrf_checks=True)

    response = csrf_client.post(
        reverse("webhooks:paypal-webhook"),
        headers=required_headers,
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
    response = caller(reverse("webhooks:paypal-webhook"))

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


@pytest.mark.parametrize(
    "header_to_remove",
    [
        "Paypal-Transmission-Time",
        "Paypal-Auth-Version",
        "Paypal-Cert-Url",
        "Paypal-Auth-Algo",
        "Paypal-Transmission-Sig",
        "Paypal-Transmission-Id",
        "Correlation-Id",
    ],
)
def test_not_found_if_any_required_header_is_missing(
    client, required_headers, header_to_remove
):
    test_headers = dict(required_headers)
    test_headers.pop(header_to_remove, None)

    response = client.post(
        reverse("webhooks:paypal-webhook"),
        headers=test_headers,
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
