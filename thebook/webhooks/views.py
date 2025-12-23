from http import HTTPStatus

import structlog

from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from thebook.webhooks.models import OpenPixWebhookPayload, PaypalWebhookPayload

logger = structlog.get_logger(__name__)


@method_decorator(csrf_exempt, "dispatch")
@method_decorator(login_not_required, "dispatch")
class OpenPixWebhook(View):

    http_method_names = [
        "post",
    ]

    required_headers = ("X-OpenPix-Signature", "X-TheBook-Token")

    def post(self, request, *args, **kwargs):
        logger.info("openpix.webhook.received")

        if not all(
            required_header in request.headers
            for required_header in self.required_headers
        ):
            logger.warning("openpix.webhook.missing_required_headers")
            return HttpResponse(status=HTTPStatus.NOT_FOUND)

        openpix_webhook_payload = OpenPixWebhookPayload.objects.create(
            thebook_token=request.headers["X-TheBook-Token"],
            payload=request.body.decode("utf-8"),
        )
        logger.info(
            "openpix.webhook.openpix_webhook_payload.created",
            id_=openpix_webhook_payload.id,
        )

        openpix_webhook_payload.process()

        return HttpResponse(status=HTTPStatus.OK)


@method_decorator(csrf_exempt, "dispatch")
@method_decorator(login_not_required, "dispatch")
class PaypalWebhook(View):
    http_method_names = [
        "post",
    ]

    required_headers = (
        "Paypal-Transmission-Time",
        "Paypal-Auth-Version",
        "Paypal-Cert-Url",
        "Paypal-Auth-Algo",
        "Paypal-Transmission-Sig",
        "Paypal-Transmission-Id",
        "Correlation-Id",
    )

    def post(self, request, *args, **kwargs):
        logger.info("paypal.webhook.received")

        if not all(
            required_header in request.headers
            for required_header in self.required_headers
        ):
            logger.warning("paypal.webhook.missing_required_headers")
            return HttpResponse(status=HTTPStatus.NOT_FOUND)

        webhook_data = {
            "paypal_transmission_time": request.headers["Paypal-Transmission-Time"],
            "paypal_auth_version": request.headers["Paypal-Auth-Version"],
            "paypal_cert_url": request.headers["Paypal-Cert-Url"],
            "paypal_auth_algo": request.headers["Paypal-Auth-Algo"],
            "paypal_transmission_sig": request.headers["Paypal-Transmission-Sig"],
            "paypal_transmission_id": request.headers["Paypal-Transmission-Id"],
            "correlation_id": request.headers["Correlation-Id"],
            "payload": request.body.decode("utf-8"),
        }
        paypal_webhook_payload = PaypalWebhookPayload.objects.create(**webhook_data)
        logger.info(
            "paypal.webhook.paypal_webhook_payload.created",
            id_=paypal_webhook_payload.id,
        )

        return HttpResponse(status=HTTPStatus.OK)
