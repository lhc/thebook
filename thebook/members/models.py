import calendar
import datetime
import itertools
import re

from dateutil.relativedelta import relativedelta
from localflavor.br.models import BRCPFField

from django.conf import settings
from django.db import models
from django.db.models import UniqueConstraint
from django.utils.functional import classproperty
from django.utils.translation import gettext as _

from thebook.members.managers import ReceivableFeeManager


class FeeIntervals:
    MONTHLY = 1
    QUARTERLY = 3
    BIANNUALLY = 6
    ANNUALLY = 12

    @classproperty
    def choices(cls):
        return (
            (cls.MONTHLY, _("Monthly")),
            (cls.QUARTERLY, _("Quarterly")),
            (cls.BIANNUALLY, _("Biannually")),
            (cls.ANNUALLY, _("Annually")),
        )


class FeePaymentStatus:
    PAID = 1
    UNPAID = 2
    DUE = 3
    SKIPPED = 4

    @classproperty
    def choices(cls):
        return (
            (cls.PAID, _("Paid")),
            (cls.UNPAID, _("Unpaid")),
            (cls.DUE, _("Due")),
            (cls.SKIPPED, _("Skipped")),
        )


class PaymentMethod:
    PAYPAL = 1
    PIX = 2
    PIX_RECURRING = 3

    @classproperty
    def choices(cls):
        return (
            (cls.PAYPAL, _("PayPal")),
            (cls.PIX, _("Pix")),
            (cls.PIX_RECURRING, _("Recurring Pix")),
        )


class Membership(models.Model):
    member = models.OneToOneField(
        "members.Member",
        on_delete=models.CASCADE,
        primary_key=True,
    )

    start_date = models.DateField(verbose_name=_("Start Membership"))
    end_date = models.DateField(verbose_name=_("End Membership"), null=True, blank=True)
    membership_fee_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name=_("Membership Fee"),
        help_text=_("The amount to be paid in the chosen interval"),
    )
    payment_interval = models.IntegerField(
        choices=FeeIntervals.choices,
        verbose_name=_("Payment Interval"),
        help_text=_("How often does the member pay their fees?"),
    )
    payment_method = models.IntegerField(
        choices=PaymentMethod.choices,
        default=PaymentMethod.PAYPAL,
        verbose_name=_("Payment Method"),
        help_text=_("How fees are paid?"),
    )
    active = models.BooleanField(
        default=False,
        verbose_name=_("Active Membership"),
        help_text=_(
            "Indicates is we are expecting to be receiving fees from this membership"
        ),
    )

    @classmethod
    def from_db(cls, db, field_names, values):
        new = super().from_db(db, field_names, values)
        new._original_active = new.active
        return new

    def __str__(self):
        active_status = "Active" if self.active else "Inactive"
        return f"{active_status} membership of {self.member.name}"

    def save(self, **kwargs):
        self.create_receivable_fee_transaction_match_rules()
        super().save(**kwargs)

    def create_next_receivable_fee(self, commit=True):
        if not self.active:
            return None

        def _next_period(current_date, payment_interval):
            month_increment = {
                FeeIntervals.MONTHLY: 1,
                FeeIntervals.QUARTERLY: 3,
                FeeIntervals.BIANNUALLY: 6,
                FeeIntervals.ANNUALLY: 12,
            }
            next_possible_month = current_date.month + month_increment[payment_interval]

            if (
                next_possible_month % 12 == next_possible_month
                or next_possible_month % 12 == 0
            ):
                next_month = next_possible_month
                next_year = current_date.year
            else:
                next_month = next_possible_month % 12
                next_year = current_date.year + 1

            return next_month, next_year

        last_receivable_fee = self.receivable_fees.order_by("-start_date").first()
        if last_receivable_fee is None:
            _, last_day_of_month = calendar.monthrange(
                self.start_date.year, self.start_date.month
            )
            start_date = datetime.date(self.start_date.year, self.start_date.month, 1)
            due_date = datetime.date(
                self.start_date.year, self.start_date.month, last_day_of_month
            )
        else:
            next_month, next_year = _next_period(
                last_receivable_fee.start_date, self.payment_interval
            )
            _, last_day_of_month = calendar.monthrange(next_year, next_month)
            start_date = datetime.date(next_year, next_month, 1)
            due_date = datetime.date(next_year, next_month, last_day_of_month)

        receivable_fee = ReceivableFee(
            membership=self,
            start_date=start_date,
            due_date=due_date,
            amount=self.membership_fee_amount,
            status=FeePaymentStatus.UNPAID,
        )
        if commit:
            receivable_fee.save()

        return receivable_fee

    def create_receivable_fee_transaction_match_rules(self):
        member_cpf = self.member.cpf
        member_cpf_only_digits = re.sub(r"[^\d]+", "", member_cpf)

        pattern_1 = f".*{self.member.name.lower()}.*"
        ReceivableFeeTransactionMatchRule.objects.get_or_create(
            membership=self, pattern=pattern_1
        )

        if not member_cpf_only_digits:
            return

        pattern_2 = f".*{member_cpf_only_digits}.*"
        ReceivableFeeTransactionMatchRule.objects.get_or_create(
            membership=self, pattern=pattern_2
        )

        pattern_3 = f".*{member_cpf_only_digits[:3]}.{member_cpf_only_digits[3:6]}.{member_cpf_only_digits[6:9]}-{member_cpf_only_digits[9:]}.*"
        ReceivableFeeTransactionMatchRule.objects.get_or_create(
            membership=self, pattern=pattern_3
        )

    @property
    def next_membership_fee_payment_date(self):
        allowed_months = sorted(
            [
                month
                for month in itertools.islice(
                    [
                        _month
                        for _month in itertools.islice(
                            itertools.cycle(range(1, 13)), self.start_date.month - 1, 25
                        )
                    ],
                    12,
                )
            ][:: self.payment_interval]
        )

        today = datetime.date.today()
        for month in range(today.month + 1, 13):
            if month in allowed_months:
                next_payment_year = today.year
                next_payment_month = month
                break
        else:
            next_payment_year = today.year + 1
            next_payment_month = allowed_months[0]

        _, last_day_of_next_payment_month = calendar.monthrange(
            next_payment_year, next_payment_month
        )

        next_payment_day = min([self.start_date.day, last_day_of_next_payment_month])

        return datetime.date(next_payment_year, next_payment_month, next_payment_day)

    @property
    def debtor(self):
        return self.receivable_fees.due().exists()


class Member(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    has_key = models.BooleanField(default=False, verbose_name=_("Has physical key?"))
    phone_number = models.CharField(
        max_length=32, blank=True, verbose_name=_("Phone number")
    )
    cpf = BRCPFField(blank=True, default="", verbose_name=_("CPF"))

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def can_have_key(self):
        return self.membership.start_date < datetime.date.today() - relativedelta(
            months=3
        )


class ReceivableFee(models.Model):
    membership = models.ForeignKey(
        to="members.Membership",
        on_delete=models.CASCADE,
        related_name="receivable_fees",
    )

    start_date = models.DateField(
        verbose_name=_("Expected start date of receiving period")
    )
    due_date = models.DateField(verbose_name=_("Due date"))
    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name=_("Fee Amount"),
    )
    status = models.IntegerField(
        choices=FeePaymentStatus.choices,
        default=FeePaymentStatus.UNPAID,
        verbose_name=_("Payment Status"),
    )
    transaction = models.ForeignKey(
        "bookkeeping.Transaction",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["membership", "start_date"],
                name="unique_receivable_fee_in_month",
            )
        ]

    objects = ReceivableFeeManager()

    def paid_with(self, transaction):
        self.status = FeePaymentStatus.PAID
        self.transaction = transaction
        self.save()

        return self


class ReceivableFeeTransactionMatchRule(models.Model):
    pattern = models.CharField(max_length=512)
    membership = models.ForeignKey(
        "members.Membership",
        on_delete=models.CASCADE,
    )
