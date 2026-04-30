from django.urls import path

from thebook.members import views

app_name = "members"

urlpatterns = [
    path(
        "membership_form/<uuid:membership_form_uuid>/",
        views.membership_form,
        name="membership-form",
    ),
    path(
        "create",
        views.new_member,
        name="create-member",
    ),
    path(
        "list",
        views.members_list,
        name="members-list",
    ),
]
