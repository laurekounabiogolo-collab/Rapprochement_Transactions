from django.urls import path

from .views import importation, telecharger_erreurs_import

urlpatterns = [
    path("", importation, name="importation"),
    path("<int:pk>/erreurs.csv", telecharger_erreurs_import, name="telecharger_erreurs_import"),
]
