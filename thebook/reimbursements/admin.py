from django.contrib import admin

from thebook.reimbursements.models import ReimbursementRequest


@admin.register(ReimbursementRequest)
class ReimbursementRequestAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "value",
        "date",
        "description",
        "status",
    ]
    list_filter = [
        "status",
    ]
