from django.db import models


class SourceDonnees(models.Model):

    class TypeSource(models.TextChoices):
        PARTENAIRE = 'PARTENAIRE', 'Partenaire de transfert'
        BANQUE = 'BANQUE', 'Système bancaire'

    nom = models.CharField(max_length=100, unique=True)

    type_source = models.CharField(
        max_length=20,
        choices=TypeSource.choices
    )

    description = models.TextField(blank=True)

    actif = models.BooleanField(default=True)

    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom