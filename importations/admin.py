from django.contrib import admin

from importations.models import FichierImporte


@admin.register(FichierImporte)
class FichierImporteAdmin(admin.ModelAdmin):
    list_display = ("nom_fichier", "source", "type_operation", "statut", "date_importation")
    list_filter = ("source", "statut", "type_operation")
