from django.shortcuts import render

from thebook.reimbursements.forms import CreateReimbursementRequestForm


def create_reimbursement(request):
    if request.method == "POST":
        form = CreateReimbursementRequestForm(request.POST)
        if form.is_valid():
            return HttpResponse("Reimbursement request received!")
    else:
        form = CreateReimbursementRequestForm()

    return render(request, "reimbursements/create.html", context={"form": form})
