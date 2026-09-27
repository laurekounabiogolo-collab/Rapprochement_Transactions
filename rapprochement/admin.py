from django.contrib import admin

from rapprochement.models import Anomalie, Correspondance, NonRapprochee, Rapprochement


@admin.register(Rapprochement)
class RapprochementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "partenaire",
        "type_operation",
        "statut",
        "nombre_correspondances",
        "nombre_anomalies",
        "valide",
        "date_lancement",
    )
    list_filter = ("statut", "valide", "type_operation", "partenaire")


@admin.register(Correspondance)
class CorrespondanceAdmin(admin.ModelAdmin):
    list_display = ("id", "rapprochement", "transaction_1", "score_correspondance", "validee")


@admin.register(Anomalie)
class AnomalieAdmin(admin.ModelAdmin):
    list_display = ("id", "type_anomalie", "statut", "transaction", "resolue_par", "date_creation")
    list_filter = ("type_anomalie", "statut")


@admin.register(NonRapprochee)
class NonRapprocheeAdmin(admin.ModelAdmin):
    list_display = ("id", "rapprochement", "transaction", "cote")
