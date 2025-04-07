from django.contrib.auth.decorators import login_not_required
from django.shortcuts import render

from thebook.reimbursements.forms import CreateReimbursementRequestForm


@login_not_required
def create_reimbursement(request):
    if request.method == "POST":
        form = CreateReimbursementRequestForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()

            new_form = CreateReimbursementRequestForm()
            return render(
                request,
                "reimbursements/create.html",
                context={
                    "form": new_form,
                    "success_message": f"Sua solicitação de reembolso foi recebida com sucesso. Você receberá atualizações no endereço de e-mail '{form.cleaned_data['email']}'",
                },
            )
    else:
        form = CreateReimbursementRequestForm()

    return render(request, "reimbursements/create.html", context={"form": form})
