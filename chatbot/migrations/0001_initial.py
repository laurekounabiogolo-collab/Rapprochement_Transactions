from django.db import migrations, models


def creer_intentions_initiales(apps, schema_editor):
    Intention = apps.get_model("chatbot", "Intention")
    donnees = [
        ("SALUTATION", "Salutation", ["Bonjour", "Salut", "Bonjour tu peux m’aider ?", "Bonsoir"],
         "Bonjour ! Je peux t’aider à utiliser l’application de rapprochement."),
        ("AIDE_IMPORTATION", "Aide à l’importation",
         ["Comment importer un fichier ?", "Où charger mon CSV ?", "Comment ajouter les transactions ?", "Quels fichiers dois-je importer ?"],
         "Importe d’abord le fichier du partenaire puis le fichier Amplitude avec le même type d’opération. Ensuite lance le rapprochement."),
        ("AIDE_RAPPROCHEMENT", "Aide au rapprochement",
         ["Comment fonctionne le rapprochement ?", "Quels champs sont comparés ?", "Est-ce que la date est vérifiée ?", "Comment le système trouve une correspondance ?"],
         "Le système compare les références et les champs financiers prévus pour le type d’opération. La date n’est pas utilisée comme critère actuellement."),
        ("EXPLIQUER_ANOMALIE", "Expliquer une anomalie",
         ["Que signifie une anomalie ?", "Pourquoi cette transaction a une anomalie ?", "Que veut dire différence de MTTC ?", "Pourquoi le montant ne correspond pas ?"],
         "Une anomalie est signalée lorsqu’une référence correspond mais qu’un critère financier comparé présente un écart. Consulte les détails pour voir lequel."),
        ("EXPLIQUER_STATUT", "Expliquer un statut",
         ["Que veut dire non rapprochée ?", "Quelle différence entre anomalie et résolue ?", "Que signifie en attente ?", "Une anomalie résolue devient-elle une correspondance ?"],
         "Le statut indique le résultat du rapprochement ou le suivi d’une anomalie. Résolue signifie que l’anomalie a été traitée mais cela ne transforme pas automatiquement la transaction en correspondance."),
    ]
    for code, nom, exemples, reponse in donnees:
        Intention.objects.update_or_create(
            code=code,
            defaults={"nom": nom, "exemples": "\n".join(exemples), "reponse": reponse, "active": True},
        )


def supprimer_intentions_initiales(apps, schema_editor):
    Intention = apps.get_model("chatbot", "Intention")
    Intention.objects.filter(code__in=[
        "SALUTATION", "AIDE_IMPORTATION", "AIDE_RAPPROCHEMENT",
        "EXPLIQUER_ANOMALIE", "EXPLIQUER_STATUT",
    ]).delete()


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Intention",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.SlugField(help_text="Identifiant stable, par exemple AIDE_IMPORTATION.", max_length=60, unique=True)),
                ("nom", models.CharField(max_length=120)),
                ("exemples", models.TextField(help_text="Une question ou expression par ligne. Ce sont les exemples appris par le modèle.")),
                ("reponse", models.TextField()),
                ("active", models.BooleanField(default=True)),
                ("modifie_le", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ("nom",)},
        ),
        migrations.RunPython(creer_intentions_initiales, supprimer_intentions_initiales),
    ]
