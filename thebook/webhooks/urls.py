from django.urls import path

from thebook.webhooks import views

app_name = "webhooks"

urlpatterns = [
    path(
        "openpix",
        views.OpenPixWebhook.as_view(),
        name="openpix-webhook",
    ),
    path(
        "paypal",
        views.PaypalWebhook.as_view(),
        name="paypal-webhook",
    ),
]
