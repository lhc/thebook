import datetime
from decimal import Decimal
from pathlib import Path

import pytest
import responses
from freezegun import freeze_time
from model_bakery import baker

from django.conf import settings

from thebook.bookkeeping.models import Transaction
from thebook.webhooks.models import PaypalWebhookPayload, ProcessingStatus

SAMPLE_PAYLOADS_DIR = Path(__file__).parent / "sample_payloads"


@pytest.fixture
def paypal__oauth2_token():
    return {"access_token": "test-access-token"}


@pytest.fixture
def paypal__brl_payload__subscription():
    with open(
        Path(SAMPLE_PAYLOADS_DIR / "paypal__brl_payload__subscription.json"), "r"
    ) as payload:
        return payload.read()


@pytest.fixture
def webhook__brl_payload():
    with open(Path(SAMPLE_PAYLOADS_DIR / "webhook__brl_payload.json"), "r") as payload:
        return payload.read()


@pytest.fixture
def paypal__usd_payload__subscription():
    with open(
        Path(SAMPLE_PAYLOADS_DIR / "paypal__usd_payload__subscription.json"), "r"
    ) as payload:
        return payload.read()


@pytest.fixture
def webhook__usd_payload():
    with open(Path(SAMPLE_PAYLOADS_DIR / "webhook__usd_payload.json"), "r") as payload:
        return payload.read()


@responses.activate
def test_payment_sale_completed__usd_transaction(
    db, webhook__usd_payload, paypal__oauth2_token, paypal__usd_payload__subscription
):
    responses.add(
        responses.POST,
        f"{settings.PAYPAL_API_BASE_URL}/v1/oauth2/token",
        json=paypal__oauth2_token,
    )
    responses.add(
        responses.GET,
        f"{settings.PAYPAL_API_BASE_URL}/v1/billing/subscriptions/I-AAAAAAAAAAAA",
        body=paypal__usd_payload__subscription,
        content_type="application/json",
    )

    webhook_payload = baker.make(
        PaypalWebhookPayload,
        payload=webhook__usd_payload,
    )

    webhook_payload.process()
    webhook_payload.refresh_from_db()
    assert webhook_payload.status == ProcessingStatus.PROCESSED

    transaction = Transaction.objects.get(reference="0PAAAAAAAAAAAAAAA")
    assert transaction.date == datetime.date(2026, 2, 12)
    assert transaction.description == "Elvis Presley - Q64J6VDR3DBHN"
    assert transaction.amount == Decimal("231.93")

    # Do not create transaction with bank fees. Total received amount already in transaction above
    assert not Transaction.objects.filter(reference="T0PAAAAAAAAAAAAAAA").exists()


@responses.activate
def test_payment_sale_completed__brl_transaction(
    db, webhook__brl_payload, paypal__oauth2_token, paypal__brl_payload__subscription
):
    responses.add(
        responses.POST,
        f"{settings.PAYPAL_API_BASE_URL}/v1/oauth2/token",
        json=paypal__oauth2_token,
    )
    responses.add(
        responses.GET,
        f"{settings.PAYPAL_API_BASE_URL}/v1/billing/subscriptions/I-BBBBBBBBBBBB",
        body=paypal__brl_payload__subscription,
        content_type="application/json",
    )

    webhook_payload = baker.make(
        PaypalWebhookPayload,
        payload=webhook__brl_payload,
    )

    webhook_payload.process()
    webhook_payload.refresh_from_db()
    assert webhook_payload.status == ProcessingStatus.PROCESSED

    transaction = Transaction.objects.get(reference="35R35201NA4015510")
    assert transaction.date == datetime.date(2026, 2, 13)
    assert transaction.description == "Bruce Wayne - L4AVQLJR8GMZY"
    assert transaction.amount == Decimal("85")

    # Transactions in BRL must have a bank fee extra transaction
    bank_fee_transaction = Transaction.objects.get(reference="T35R35201NA4015510")
    assert bank_fee_transaction.date == datetime.date(2026, 2, 13)
    assert (
        bank_fee_transaction.description == "Taxa PayPal - Bruce Wayne - L4AVQLJR8GMZY"
    )
    assert bank_fee_transaction.amount == Decimal("-4.67")
