from django.db import models
from transactions.models import Transaction
from utilisateurs.models import Utilisateur
from SourceDonnees.models import SourceDonnees
from importations.models import FichierImporte


class Rapprochement(models.Model):

    class TypeOperation(models.TextChoices):
        ENVOI = 'ENVOI', 'Envoi'
        RETRAIT = 'RETRAIT', 'Retrait / Paiement'
        REMBOURSEMENT = 'REMBOURSEMENT', 'Remboursement'

    class Statut(models.TextChoices):
        EN_COURS = 'EN_COURS', 'En cours'
        TERMINE = 'TERMINE', 'Terminé'
        TERMINE_AVEC_ANOMALIES = (
            'TERMINE_AVEC_ANOMALIES',
            'Terminé avec anomalies'
        )

    date_lancement = models.DateTimeField(
        auto_now_add=True
    )

    lance_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.PROTECT,
        related_name='rapprochements_lances'
    )

    partenaire = models.ForeignKey(
        SourceDonnees,
        on_delete=models.PROTECT,
        related_name='rapprochements'
    )

    fichier_partenaire = models.ForeignKey(
        FichierImporte,
        on_delete=models.PROTECT,
        related_name='rapprochements_partenaire'
    )

    fichier_amplitude = models.ForeignKey(
        FichierImporte,
        on_delete=models.PROTECT,
        related_name='rapprochements_amplitude'
    )

    type_operation = models.CharField(
        max_length=20,
        choices=TypeOperation.choices
    )

    statut = models.CharField(
        max_length=30,
        choices=Statut.choices,
        default=Statut.EN_COURS
    )

    nombre_transactions = models.PositiveIntegerField(
        default=0
    )

    nombre_correspondances = models.PositiveIntegerField(
        default=0
    )

    nombre_anomalies = models.PositiveIntegerField(
        default=0
    )

    nombre_non_rapprochees = models.PositiveIntegerField(
        default=0
    )

    message = models.TextField(blank=True)

    valide = models.BooleanField(default=False)

    valide_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rapprochements_valides'
    )

    date_validation = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Rapprochement {self.id} - {self.partenaire.nom}"


class Correspondance(models.Model):

    rapprochement = models.ForeignKey(
        Rapprochement,
        on_delete=models.CASCADE,
        related_name='correspondances'
    )

    transaction_1 = models.ForeignKey(
        Transaction,
        on_delete=models.PROTECT,
        related_name='correspondances_1'
    )

    transaction_2 = models.ForeignKey(
        Transaction,
        on_delete=models.PROTECT,
        related_name='correspondances_2'
    )

    score_correspondance = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    automatique = models.BooleanField(
        default=True
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    validee = models.BooleanField(default=False)

    validee_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='correspondances_validees'
    )

    date_validation = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return (
            f"Correspondance {self.id} - "
            f"Score : {self.score_correspondance}%"
        )


class Anomalie(models.Model):

    class TypeAnomalie(models.TextChoices):
        MONTANT = 'MONTANT', 'Différence de montant'
        TVA = 'TVA', 'Différence de TVA'
        TTA = 'TTA', 'Différence de TTA'
        CTE = 'CTE', 'Différence de CTE'
        MTTC = 'MTTC', 'Différence de MTTC'
        DATE = 'DATE', 'Différence de date'
        REFERENCE = 'REFERENCE', 'Référence différente'
        DONNEES = 'DONNEES', 'Données différentes'
        REGLEMENTATION = 'REGLEMENTATION', 'Non-conformité réglementaire'
        ABSENCE = 'ABSENCE', 'Transaction absente'
        DOUBLON = 'DOUBLON', 'Transaction en double'
        AUTRE = 'AUTRE', 'Autre'

    class Statut(models.TextChoices):
        NON_TRAITEE = 'NON_TRAITEE', 'Non traitée'
        EN_COURS = 'EN_COURS', 'En cours'
        RESOLUE = 'RESOLUE', 'Résolue'

    rapprochement = models.ForeignKey(
        Rapprochement,
        on_delete=models.CASCADE,
        related_name='anomalies'
    )

    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.PROTECT,
        related_name='anomalies'
    )

    type_anomalie = models.CharField(
        max_length=30,
        choices=TypeAnomalie.choices
    )

    description = models.TextField()

    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.NON_TRAITEE
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    resolue_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='anomalies_resolues'
    )

    date_resolution = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Anomalie {self.id} - {self.type_anomalie}"


class NonRapprochee(models.Model):

    class Cote(models.TextChoices):
        PARTENAIRE = 'PARTENAIRE', 'Partenaire'
        AMPLITUDE = 'AMPLITUDE', 'Amplitude'

    rapprochement = models.ForeignKey(
        Rapprochement,
        on_delete=models.CASCADE,
        related_name='non_rapprochees'
    )

    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.PROTECT,
        related_name='non_rapprochees'
    )

    cote = models.CharField(
        max_length=20,
        choices=Cote.choices,
        default=Cote.PARTENAIRE
    )

    description = models.TextField(blank=True)

    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Non rapprochée {self.transaction.reference}"