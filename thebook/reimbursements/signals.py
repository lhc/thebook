from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from thebook.reimbursements.models import ReimbursementRequest, RequestStatus


def _accept_request(reimbursement_request): ...


def _complete_request(reimbursement_request): ...


def _reject_request(reimbursement_request): ...


def _received_request(reimbursement_request):
    send_mail(
        "[thebook] Solicitação de reembolso enviada",
        render_to_string(
            "emails/reimbursement_request_sent.txt",
            context={"reimbursement_request": reimbursement_request},
        ),
        "reembolso@lhc.net.br",
        [
            reimbursement_request.email,
        ],
        fail_silently=False,
    )
    send_mail(
        "[thebook] Solicitação de reembolso recebida",
        render_to_string(
            "emails/reimbursement_request_received.txt",
            context={"reimbursement_request": reimbursement_request},
        ),
        "reembolso@lhc.net.br",
        settings.REIMBURSEMENT_REQUEST_EMAILS,
        fail_silently=False,
    )


STATUS_TRANSITIONS = {
    (RequestStatus.RECEIVED, RequestStatus.ACCEPTED): _accept_request,
    (RequestStatus.ACCEPTED, RequestStatus.COMPLETED): _complete_request,
    (RequestStatus.RECEIVED, RequestStatus.REJECTED): _reject_request,
    (RequestStatus.ACCEPTED, RequestStatus.REJECTED): _reject_request,
}


@receiver(pre_save, sender=ReimbursementRequest)
def validate_status_change(sender, instance, **kwargs):
    if instance.id is None:
        # Allow creating request in any status
        return

    if (instance._original_status, instance.status) not in STATUS_TRANSITIONS:
        raise ValueError(_("Status transition not allowed."))


@receiver(post_save, sender=ReimbursementRequest)
def check_status_changed(sender, instance, created, **kwargs):
    if created:
        _received_request(instance)
        return

    post_status_task = STATUS_TRANSITIONS.get(
        (instance._original_status, instance.status)
    )
    if post_status_task is None:
        return

    post_status_task(instance)
