import os
import django

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

django.setup()


from importations.services import lire_fichier


donnees = lire_fichier("transactions_test.csv")

print(donnees)


print(f"{len(donnees)} transactions lues.")
for _, ligne in donnees.iterrows():

    print(
        ligne["reference"],
        ligne["montant"],
        ligne["nom_beneficiaire"]
    )