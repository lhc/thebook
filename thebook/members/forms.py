import datetime
from decimal import Decimal

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError

from thebook.members.models import Membership, Member, FeeIntervals


class NewMemberForm(forms.Form):
    email = forms.EmailField(
        label=_("Email"),
        help_text=_("Você usará esse email para efetuar login no sistema"),
    )
    password = forms.CharField(label=_("Senha"), widget=forms.PasswordInput)
    password_confirm = forms.CharField(
        label=_("Confirme a senha"), widget=forms.PasswordInput
    )

    first_name = forms.CharField(
        label=_("Nome"),
    )
    last_name = forms.CharField(
        label=_("Sobrenome"),
        help_text=_(
            "Precisamos do seu nome completo real para questões formais da Associação (nosso CNPJ)"
        ),
    )

    name = forms.CharField(label=_("Nome que gostaria de ser chamada"))

    has_key = forms.BooleanField(
        label=_("Já possui as chaves físicas de acesso ao LHC?"), required=False
    )
    phone_number = forms.CharField(label=_("Telefone"), help_text=_("Para emergências"))

    membership_fee = forms.ChoiceField(
        label=_("Mensalidade / Anuidade"),
        choices=[
            ("85", _("R$85 / mês")),
            ("110", _("R$110 / mês")),
            ("1020", _("R$1020 / ano")),
            ("1320", _("R$1320 / ano")),
        ],
        help_text=_(
            "Qual o valor de mensalidade/anuidade você está pagando no momento?"
        ),
    )

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("password") != cleaned_data.get("password_confirm"):
            raise ValidationError("Senha e confirmação de senha não são iguais")

    def clean_email(self):
        value = self.cleaned_data["email"]

        if get_user_model().objects.filter(email=value).count() != 0:
            raise ValidationError(
                "Já existe uma pessoa associada cadastrada com esses dados"
            )

        return value

    def save(self):
        user = get_user_model().objects.create_user(
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
        )
        member = Member.objects.create(
            name=self.cleaned_data["name"],
            user=user,
            email=self.cleaned_data["email"],
            has_key=self.cleaned_data["has_key"],
            phone_number=self.cleaned_data["phone_number"],
        )

        membership_fee_amount = Decimal(self.cleaned_data["membership_fee"])
        payment_interval = (
            FeeIntervals.MONTHLY
            if membership_fee_amount <= Decimal("110")
            else FeeIntervals.ANNUALLY
        )
        membership = Membership.objects.create(
            member=member,
            membership_fee_amount=membership_fee_amount,
            payment_interval=payment_interval,
            start_date=datetime.date.today(),
            active=False,
        )
