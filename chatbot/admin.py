from django.contrib import admin

from chatbot.models import Intention


@admin.register(Intention)
class IntentionAdmin(admin.ModelAdmin):
    list_display = ("nom", "code", "active", "modifie_le")
    list_filter = ("active",)
    search_fields = ("nom", "code", "exemples", "reponse")
