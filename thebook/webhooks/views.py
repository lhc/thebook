import logging
from http import HTTPStatus

from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

logger = logging.getLogger(__name__)


@method_decorator(login_not_required, "dispatch")
class OpenPixWebhook(View):

    http_method_names = [
        "post",
    ]

    required_headers = ("X-OpenPix-Signature", "X-TheBook-Token")

    def post(self, request, *args, **kwargs):
        body = request.body.decode("utf-8")
        logger.info("Received: %s", body)

        if not all(
            required_header in request.headers
            for required_header in self.required_headers
        ):
            return HttpResponse(status=HTTPStatus.NOT_FOUND)

        return HttpResponse(status=HTTPStatus.OK)
