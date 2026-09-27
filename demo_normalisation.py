import os
import django

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

django.setup()

from importations.services import (
    lire_fichier,
    normaliser_colonnes_source
)


donnees = lire_fichier("transactions_test.csv")

print("Colonnes avant :")
print(donnees.columns.tolist())


donnees = normaliser_colonnes_source(
    donnees,
    "amplitude"
)

print("\nColonnes après :")
print(donnees.columns.tolist())

print("\nDonnées :")
print(donnees)