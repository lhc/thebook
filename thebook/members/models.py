import calendar
import datetime
import itertools

from django.conf import settings
from django.db import models
from django.utils.functional import classproperty
from django.utils.translation import gettext as _

from thebook.members.managers import ReceivableFeeManager
from django.db.models import UniqueConstraint


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

    @classproperty
    def choices(cls):
        return (
            (cls.PAID, _("Paid")),
            (cls.UNPAID, _("Unpaid")),
            (cls.DUE, _("Due")),
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
    active = models.BooleanField(
        default=True,
        verbose_name=_("Active Membership"),
        help_text=_(
            "Indicates is we are expecting to be receiving fees from this membership"
        ),
    )

    def __str__(self):
        active_status = "Active" if self.active else "Inactive"
        return f"{active_status} membership of {self.member.name}"

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


class Member(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    has_key = models.BooleanField(default=False, verbose_name=_("Has physical key?"))
    phone_number = models.CharField(
        max_length=16, blank=True, verbose_name=_("Phone number")
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


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

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["membership", "start_date"],
                name="unique_receivable_fee_in_month",
            )
        ]

    objects = ReceivableFeeManager()
