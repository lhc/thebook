from django.contrib.auth.decorators import login_not_required
from django.http import Http404
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from thebook.members.forms import NewMemberForm
from thebook.members.models import Member, MembershipForm


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


@login_not_required
def membership_form(request, membership_form_uuid):
    membership_form_obj = get_object_or_404(MembershipForm, uuid=membership_form_uuid)
    if not membership_form_obj.is_still_valid:
        raise Http404()

    if request.method == "POST":
        form = NewMemberForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("login"))
    else:
        form = NewMemberForm()

    return render(request, "members/new_member.html", {"form": form})
