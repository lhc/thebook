import uuid
from pathlib import Path

from django.db import models
from django.utils.translation import gettext as _


def upload_path(instance, filename):
    filepath = Path(filename)
    extension = filepath.suffix
    new_filename = "".join([uuid.uuid4().hex, extension])
    return Path("reimbursements", new_filename)


class RequestStatus(models.IntegerChoices):
    RECEIVED = 1, _("received")
    ACCEPTED = 2, _("accepted")
    COMPLETED = 3, _("completed")
    REJECTED = 4, _("rejected")


class ReimbursementRequest(models.Model):
    name = models.CharField(max_length=254)
    email = models.EmailField()
    value = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    description = models.TextField()
    payment_info = models.TextField()
    document = models.FileField(upload_to=upload_path)
    status = models.IntegerField(
        choices=RequestStatus.choices,
        default=RequestStatus.RECEIVED,
    )

    @classmethod
    def from_db(cls, db, field_names, values):
        new = super().from_db(db, field_names, values)
        new._original_status = new.status
        return new

    def accept(self, message=None):
        self._accept_message = message
        self.status = RequestStatus.ACCEPTED
        self.save()

    def complete(self, message=None):
        self._complete_message = message
        self.status = RequestStatus.COMPLETED
        self.save()

    def reject(self, message=None):
        self._reject_message = message
        self.status = RequestStatus.REJECTED
        self.save()
