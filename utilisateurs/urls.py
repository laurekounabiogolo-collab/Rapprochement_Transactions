from django.urls import path

from .views import (
    connexion,
    creer_utilisateur,
    dashboard,
    deconnexion,
    desactiver_utilisateur,
    supprimer_utilisateur,
    liste_utilisateurs,
    modifier_utilisateur,
)

urlpatterns = [
    path("", connexion, name="connexion"),
    path("dashboard/", dashboard, name="dashboard"),
    path("deconnexion/", deconnexion, name="deconnexion"),
    path("utilisateurs/", liste_utilisateurs, name="liste_utilisateurs"),
    path("utilisateurs/nouveau/", creer_utilisateur, name="creer_utilisateur"),
    path("utilisateurs/<int:pk>/modifier/", modifier_utilisateur, name="modifier_utilisateur"),
    path(
        "utilisateurs/<int:pk>/statut/",
        desactiver_utilisateur,
        name="desactiver_utilisateur",
    ),
    path("utilisateurs/<int:pk>/supprimer/", supprimer_utilisateur, name="supprimer_utilisateur"),
]
