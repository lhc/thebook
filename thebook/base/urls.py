from django.urls import path

from thebook.base import views

app_name = "base"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
]
