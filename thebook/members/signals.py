import markdown

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives, send_mail
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from thebook.members.models import Membership, MembershipForm


def _send_onboarding_message(membership):
    send_mail(
        "[thebook] Boas vindas ao Laboratório Hacker de Campinas",
        render_to_string(
            "emails/onboarding.txt",
            context={"membership": membership},
        ),
        "contato@lhc.net.br",
        [membership.member.user.email],
        fail_silently=False,
    )


def _new_membership_created(membership):
    send_mail(
        "[thebook] Novo cadastro realizado",
        render_to_string(
            "emails/new_membership.txt",
            context={"membership": membership},
        ),
        "noreply@lhc.net.br",
        ["contato@lhc.net.br"],
        fail_silently=False,
    )


@receiver(post_save, sender=Membership)
def check_active_status(sender, instance, created, **kwargs):
    if created:
        _new_membership_created(instance)
        instance.create_next_receivable_fee()
        return

    if instance.active and not instance._original_active:
        # Onboarding message only sent if membership is set as active
        _send_onboarding_message(instance)


def _new_membership_form_created(membership_form):
    text_content = render_to_string(
        "emails/new_membership_form.md",
        context={"membership_form": membership_form, "site_url": settings.SITE_URL},
    )
    html_content = markdown.markdown(text_content)

    msg = EmailMultiAlternatives(
        subject="[thebook] Cadastro de pessoa associada ao LHC",
        body=text_content,
        from_email="noreply@lhc.net.br",
        to=[membership_form.email],
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()


@receiver(post_save, sender=MembershipForm)
def check_active_status(sender, instance, created, **kwargs):
    if created:
        _new_membership_form_created(instance)
        return
