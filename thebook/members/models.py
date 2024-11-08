from django.db import models
from django.utils.functional import classproperty
from django.utils.translation import gettext as _


class FeeIntervals:
    MONTHLY = 1
    QUARTERLY = 3
    BIANNUAL = 6
    ANNUALLY = 12

    @classproperty
    def choices(cls):
        return (
            (cls.MONTHLY, _("Monthly")),
            (cls.QUARTERLY, _("Quarterly")),
            (cls.BIANNUAL, _("Biannually")),
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
    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name=_("Membership Fee"),
        help_text=_("The amount to be paid in the chosen interval"),
    )
    interval = models.IntegerField(
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


class Member(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    email = models.EmailField(max_length=200, verbose_name=_("E-Mail"))
    has_key = models.BooleanField(default=False, verbose_name=_("Has physical key?"))
    phone_number = models.CharField(
        max_length=16, blank=True, verbose_name=_("Phone number")
    )

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
        verbose_name=_("Payment Status"),
    )
