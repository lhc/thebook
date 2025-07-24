from django.urls import path

from thebook.members import views

app_name = "members"

urlpatterns = [
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
