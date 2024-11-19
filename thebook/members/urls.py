from django.urls import path

from thebook.members import views

app_name = "members"

urlpatterns = [
    path(
        "new",
        views.new_member,
        name="new-member",
    ),
]
