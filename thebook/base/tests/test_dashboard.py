from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from model_bakery import baker


def test_unauthenticated_access_to_dashboard_redirect_to_login_page(db, client):
    dashboard_url = reverse("base:dashboard")

    response = client.get(dashboard_url)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f"{settings.LOGIN_URL}?next={dashboard_url}"


def test_allowed_access_dashboard_authenticated(db, client):
    user = baker.make(get_user_model())
    client.force_login(user)

    response = client.get(reverse("base:dashboard"))

    assert response.status_code == HTTPStatus.OK
