app_name = "base"

from django.urls import path
from thebook.base import views

app_name = "base"  # <- ESSENCIAL para o namespace funcionar

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
]
