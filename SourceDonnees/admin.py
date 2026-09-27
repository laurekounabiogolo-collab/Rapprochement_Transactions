from django.contrib import admin

from SourceDonnees.models import SourceDonnees


@admin.register(SourceDonnees)
class SourceDonneesAdmin(admin.ModelAdmin):
    list_display = ("nom", "type_source", "actif")
    list_filter = ("type_source", "actif")
    search_fields = ("nom", "description")
    readonly_fields = ("date_creation",)
