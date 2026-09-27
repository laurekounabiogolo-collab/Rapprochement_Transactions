from django.urls import path

from .views import (
    anomalies,
    correspondances,
    detail_anomalie,
    detail_rapprochement,
    lancer,
    liste_rapprochements,
    non_rapprochees,
    valider_correspondance,
    valider_rapprochement,
)

urlpatterns = [
    path("", liste_rapprochements, name="liste_rapprochements"),
    path("lancer/", lancer, name="lancer_rapprochement"),
    path("<int:pk>/", detail_rapprochement, name="detail_rapprochement"),
    path("<int:pk>/valider/", valider_rapprochement, name="valider_rapprochement"),
    path("correspondances/", correspondances, name="correspondances"),
    path(
        "correspondances/<int:pk>/valider/",
        valider_correspondance,
        name="valider_correspondance",
    ),
    path("anomalies/", anomalies, name="anomalies"),
    path("anomalies/<int:pk>/", detail_anomalie, name="detail_anomalie"),
    path("non-rapprochees/", non_rapprochees, name="non_rapprochees"),
]
