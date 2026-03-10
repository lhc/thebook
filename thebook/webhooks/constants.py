from django.utils.functional import classproperty
from django.utils.translation import gettext as _


class ProcessingStatus:
    RECEIVED = 1
    PROCESSED = 2
    UNPARSABLE = 3
    DUPLICATED = 4

    @classproperty
    def choices(cls):
        return (
            (cls.RECEIVED, _("Received")),
            (cls.PROCESSED, _("Processed")),
            (cls.UNPARSABLE, _("Unparsable")),
            (cls.DUPLICATED, _("Duplicated")),
        )
