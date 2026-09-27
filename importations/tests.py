from datetime import datetime
from decimal import Decimal

import pandas as pd
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from SourceDonnees.models import SourceDonnees
from importations.models import FichierImporte
from importations.regles_metier import recalculer_envoi_ria_yuba
from importations.services import (
    enregistrer_transactions,
    normaliser_colonnes_source,
    preparer_transactions,
)
from transactions.models import Transaction
from utilisateurs.models import Utilisateur


class ImportationServicesTests(TestCase):
    def setUp(self):
        SourceDonnees.objects.create(
            nom="RIA",
            type_source=SourceDonnees.TypeSource.PARTENAIRE,
        )
        SourceDonnees.objects.create(
            nom="Amplitude",
            type_source=SourceDonnees.TypeSource.BANQUE,
        )

    def test_normalisation_colonnes_ria_et_preparation(self):
        donnees = pd.DataFrame(
            [{
                "Send Order Number": " ria-001 ",
                "Amount": "1 500,50",
                "Customer Fee": "100,00",
                "Date Transaction": "24/09/2026",
            }]
        )
        donnees.columns = donnees.columns.str.lower().str.replace(" ", "_")

        resultat = preparer_transactions(normaliser_colonnes_source(donnees, "RIA"))

        self.assertEqual(resultat.loc[0, "reference"], "RIA-001")
        self.assertEqual(resultat.loc[0, "montant"], 1500.50)
        self.assertEqual(resultat.loc[0, "frais_envoi"], 100.00)
        self.assertTrue(timezone.is_aware(resultat.loc[0, "date"]))

    def test_import_ria_envoi_recalcule_les_montants_reglementaires(self):
        donnees = pd.DataFrame(
            [{
                "reference": "RIA-002",
                "montant": 1000,
                "date": timezone.make_aware(datetime(2026, 9, 24)),
                "frais_envoi": 200,
                "tta": 50,
            }]
        )

        resultat = enregistrer_transactions(
            donnees,
            "RIA",
            type_operation=Transaction.TypeOperation.ENVOI,
        )

        self.assertEqual(len(resultat["creees"]), 1)
        transaction = resultat["creees"][0]
        self.assertEqual(transaction.tva_recalculee, Decimal("38.50"))
        self.assertEqual(transaction.cte_recalculee, Decimal("5.00"))
        self.assertEqual(transaction.mttc_recalculee, Decimal("1093.50"))

    def test_un_doublon_est_ignore_sans_supprimer_la_transaction(self):
        donnees = pd.DataFrame(
            [{
                "reference": "RIA-003",
                "montant": 750,
                "date": timezone.make_aware(datetime(2026, 9, 24)),
            }]
        )

        premier = enregistrer_transactions(donnees, "RIA")
        second = enregistrer_transactions(donnees, "RIA")

        self.assertEqual(len(premier["creees"]), 1)
        self.assertEqual(len(second["creees"]), 0)
        self.assertEqual(second["ignorees"], 1)
        self.assertEqual(Transaction.objects.filter(reference="RIA-003").count(), 1)

    def test_lignes_incompletes_sont_signalees(self):
        donnees = pd.DataFrame(
            [{
                "reference": "",
                "montant": 100,
                "date": timezone.make_aware(datetime(2026, 9, 24)),
            }, {
                "reference": "RIA-004",
                "montant": None,
                "date": timezone.make_aware(datetime(2026, 9, 24)),
            }]
        )

        resultat = enregistrer_transactions(donnees, "RIA")

        self.assertEqual(len(resultat["creees"]), 0)
        self.assertEqual(len(resultat["erreurs"]), 2)
        self.assertEqual(Transaction.objects.count(), 0)


class ReglesMetierTests(TestCase):
    def test_recalcul_envoi_ria_yuba(self):
        resultat = recalculer_envoi_ria_yuba(
            Decimal("1000"), Decimal("200"), Decimal("50")
        )

        self.assertEqual(resultat["tva"], Decimal("38.5000"))
        self.assertEqual(resultat["cte"], Decimal("5.000"))
        self.assertEqual(resultat["mttc"], Decimal("1093.5000"))


class ExportErreursImportTests(TestCase):
    def setUp(self):
        self.user = Utilisateur.objects.create_user(
            username="agent-erreurs",
            email="agent-erreurs@bange.cm",
            password="MotDePasse123",
            role=Utilisateur.Roles.AGENT_ERA,
        )
        source = SourceDonnees.objects.create(
            nom="RIA",
            type_source=SourceDonnees.TypeSource.PARTENAIRE,
        )
        self.fichier = FichierImporte.objects.create(
            nom_fichier="ria_invalide.csv",
            source=source,
            format_fichier="csv",
            type_operation=Transaction.TypeOperation.ENVOI,
            importe_par=self.user,
            statut=FichierImporte.Statut.TRAITE,
            message_erreur="Ligne 3: référence manquante.\nLigne 5 (RIA-5): montant invalide.",
        )
        self.client.force_login(self.user)

    def test_telechargement_csv_des_erreurs(self):
        response = self.client.get(
            reverse("telecharger_erreurs_import", args=[self.fichier.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("attachment;", response["Content-Disposition"])
        contenu = response.content.decode("utf-8-sig")
        self.assertIn("ria_invalide.csv", contenu)
        self.assertIn("Ligne 3: référence manquante.", contenu)
        self.assertIn("Ligne 5 (RIA-5): montant invalide.", contenu)
