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
        "created_at",
    ]
    list_filter = [
        "status",
    ]
