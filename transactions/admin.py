from django.contrib import admin

from transactions.models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "source",
        "type_operation",
        "montant",
        "mttc",
        "statut",
        "date_transaction",
    )
    list_filter = ("source", "type_operation", "statut")
    search_fields = ("reference",)
