from django.db import models
from SourceDonnees.models import SourceDonnees
from importations.models import FichierImporte


class Transaction(models.Model):

    class Statut(models.TextChoices):
        EN_ATTENTE = 'EN_ATTENTE', 'En attente'
        RAPPROCHEE = 'RAPPROCHEE', 'Rapprochée'
        ANOMALIE = 'ANOMALIE', 'Anomalie'
        NON_RAPPROCHEE = 'NON_RAPPROCHEE', 'Non rapprochée'

    class TypeOperation(models.TextChoices):
        ENVOI = 'ENVOI', 'Envoi'
        RETRAIT = 'RETRAIT', 'Retrait / Paiement'
        REMBOURSEMENT = 'REMBOURSEMENT', 'Remboursement'

    reference = models.CharField(max_length=100)

    source = models.ForeignKey(
        SourceDonnees,
        on_delete=models.PROTECT,
        related_name='transactions'
    )

    fichier_importe = models.ForeignKey(
        FichierImporte,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )

    type_operation = models.CharField(
    max_length=20,
    choices=TypeOperation.choices,
    null=True,
    blank=True
    )

    date_transaction = models.DateTimeField()

    montant = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    devise = models.CharField(
        max_length=10,
        default='XAF'
    )

    tva = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )

    tta = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )

    cte = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )

    mttc = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )

    tva_recalculee = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )

    cte_recalculee = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )

    mttc_recalculee = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )

    frais_envoi = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )

    nom_emetteur = models.CharField(
        max_length=150,
        blank=True
    )

    nom_beneficiaire = models.CharField(
        max_length=150,
        blank=True
    )

    reference_externe = models.CharField(
        max_length=100,
        blank=True
    )

    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.EN_ATTENTE
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.reference} - {self.montant} {self.devise}"