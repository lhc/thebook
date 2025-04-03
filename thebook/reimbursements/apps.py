from django.apps import AppConfig


class ReimbursementsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "thebook.reimbursements"

    def ready(self):
        from . import signals
