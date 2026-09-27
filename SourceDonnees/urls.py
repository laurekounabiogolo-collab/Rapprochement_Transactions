from django.urls import path

from SourceDonnees.views import (
    changer_statut_source,
    creer_source,
    liste_sources,
    modifier_source,
)

urlpatterns = [
    path("", liste_sources, name="liste_sources"),
    path("nouvelle/", creer_source, name="creer_source"),
    path("<int:pk>/modifier/", modifier_source, name="modifier_source"),
    path("<int:pk>/statut/", changer_statut_source, name="changer_statut_source"),
]
