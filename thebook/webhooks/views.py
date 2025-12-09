from http import HTTPStatus

from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from thebook.webhooks.models import OpenPixWebhookPayload, PaypalWebhookPayload


@method_decorator(csrf_exempt, "dispatch")
@method_decorator(login_not_required, "dispatch")
class OpenPixWebhook(View):

    http_method_names = [
        "post",
    ]

    required_headers = ("X-OpenPix-Signature", "X-TheBook-Token")

    def post(self, request, *args, **kwargs):

        if not all(
            required_header in request.headers
            for required_header in self.required_headers
        ):
            return HttpResponse(status=HTTPStatus.NOT_FOUND)

        OpenPixWebhookPayload.objects.create(
            thebook_token=request.headers["X-TheBook-Token"],
            payload=request.body.decode("utf-8"),
        )

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
        if not all(
            required_header in request.headers
            for required_header in self.required_headers
        ):
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
        PaypalWebhookPayload.objects.create(**webhook_data)

        return HttpResponse(status=HTTPStatus.OK)
