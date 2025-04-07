from django.urls import path

from thebook.reimbursements import views

app_name = "reimbursements"

urlpatterns = [
    path(
        "create",
        views.create_reimbursement,
        name="reimbursements-create",
    ),
]
