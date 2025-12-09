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

    # required_headers = ("X-OpenPix-Signature", "X-TheBook-Token")

    def post(self, request, *args, **kwargs):
        # if not all(
        #     required_header in request.headers
        #     for required_header in self.required_headers
        # ):
        #     return HttpResponse(status=HTTPStatus.NOT_FOUND)

        PaypalWebhookPayload.objects.create(
            payload=request.body.decode("utf-8"),
        )

        return HttpResponse(status=HTTPStatus.OK)
