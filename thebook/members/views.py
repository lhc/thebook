from django.contrib.auth.decorators import login_not_required
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from thebook.members.forms import NewMemberForm
from thebook.members.models import Member


@login_not_required
def new_member(request):
    if request.method == "POST":
        form = NewMemberForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("login"))
    else:
        form = NewMemberForm()

    return render(request, "members/new_member.html", {"form": form})


def members_list(request):
    members = (
        Member.objects.filter(membership__active=True)
        .select_related(
            "membership",
        )
        .order_by("name")
    )
    return render(request, "members/members.html", {"members": members})
