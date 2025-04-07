from django import forms

from thebook.reimbursements.models import ReimbursementRequest


class CreateReimbursementRequestForm(forms.ModelForm):
    name = forms.CharField(label="Nome")
    email = forms.EmailField(
        label="E-mail",
        help_text="Você receberá atualizações da sua solicitação neste endereço",
    )
    value = forms.DecimalField(
        label="Valor", help_text="Precisa ser igual ao valor dos comprovantes anexados"
    )
    date = forms.DateField(label="Data", help_text="Data da despesa")
    description = forms.CharField(label="Descrição", help_text="Descreva a sua despesa")
    payment_info = forms.CharField(
        label="Informações de pagamento",
        help_text="Sua chave Pix ou dados bancários para o depósito do reembolso",
    )
    document = forms.FileField(
        label="Comprovantes",
        help_text="Anexe cópia da Nota Fiscal e/ou do recibo correspondente",
    )

    class Meta:
        model = ReimbursementRequest
        fields = [
            "name",
            "email",
            "value",
            "date",
            "description",
            "payment_info",
            "document",
        ]
