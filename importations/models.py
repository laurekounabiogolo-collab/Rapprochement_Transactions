from django.db import models
from SourceDonnees.models import SourceDonnees
from utilisateurs.models import Utilisateur


class FichierImporte(models.Model):

    class Statut(models.TextChoices):
        EN_ATTENTE = 'EN_ATTENTE', 'En attente'
        TRAITE = 'TRAITE', 'Traité'
        ERREUR = 'ERREUR', 'Erreur'

    nom_fichier = models.CharField(max_length=255)

    source = models.ForeignKey(
        SourceDonnees,
        on_delete=models.PROTECT,
        related_name='fichiers'
    )

    fichier = models.FileField(upload_to='imports/')

    format_fichier = models.CharField(max_length=10)

    type_operation = models.CharField(max_length=20, blank=True)

    empreinte = models.CharField(max_length=64, blank=True)

    date_importation = models.DateTimeField(auto_now_add=True)

    importe_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.PROTECT,
        related_name='fichiers_importes'
    )

    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.EN_ATTENTE
    )

    nombre_transactions = models.PositiveIntegerField(default=0)

    message_erreur = models.TextField(blank=True)

    def __str__(self):
        return self.nom_fichier