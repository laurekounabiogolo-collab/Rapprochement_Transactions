from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("utilisateurs.urls")),
    path("importations/", include("importations.urls")),
    path("sources/", include("SourceDonnees.urls")),
    path("rapprochements/", include("rapprochement.urls")),
    path("transactions/", include("transactions.urls")),
    path("rapports/", include("rapports.urls")),
    path("chatbot/", include("chatbot.urls")),
]

