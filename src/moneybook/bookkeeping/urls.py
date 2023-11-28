from django.urls import path

from moneybook.bookkeeping import views

urlpatterns = [
    path("", views.transactions, name="transactions"),
]
