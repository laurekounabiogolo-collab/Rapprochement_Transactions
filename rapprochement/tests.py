from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from importations.models import FichierImporte
from importations.services import importer_depuis_chemin
from rapprochement.matching import rapprocher_envoi, rapprocher_remboursement, rapprocher_retrait, rapprocher_transaction
from rapprochement.models import Anomalie, Correspondance, NonRapprochee, Rapprochement
from rapprochement.services import lancer_rapprochement
from SourceDonnees.models import SourceDonnees
from transactions.models import Transaction
from utilisateurs.models import Utilisateur


class MatchingEnvoiTests(SimpleTestCase):

    def test_correspondance_envoi(self):
        resultat = rapprocher_envoi(
            "RIA1001", "RIA1001",
            100000, 100000,
            385, 385,
            100, 100,
            500, 500,
            100985, 100985,
        )
        self.assertEqual(resultat["resultat"], "CORRESPONDANCE")
        self.assertEqual(resultat["score"], Decimal("100.00"))

    def test_anomalie_mttc(self):
        resultat = rapprocher_envoi(
            "RIA1001", "RIA1001",
            100000, 100000,
            385, 385,
            100, 100,
            500, 500,
            100985, 102885,
        )
        self.assertEqual(resultat["resultat"], "ANOMALIE")
        self.assertGreater(resultat["ecart_mttc"], 0)
        self.assertEqual(resultat["score"], Decimal("90.00"))

    def test_non_rapprochee_reference(self):
        resultat = rapprocher_envoi(
            "RIA1001", "RIA9999",
            100000, 100000,
            385, 385,
            100, 100,
            500, 500,
            100985, 100985,
        )
        self.assertEqual(resultat["resultat"], "NON_RAPPROCHEE")

    def test_remboursement(self):
        resultat = rapprocher_remboursement("R1", "R1", 1000, 1000)
        self.assertEqual(resultat["resultat"], "CORRESPONDANCE")

    def test_correspondance_retrait_par_pin_et_tta(self):
        resultat = rapprocher_retrait(
            reference_partenaire="PIN1001",
            reference_amplitude="PIN1001",
            frais_retrait_partenaire=5000,
            tta_amplitude=100,
        )
        self.assertEqual(resultat["resultat"], "CORRESPONDANCE")
        self.assertEqual(resultat["tta_attendue"], Decimal("100.00"))
        self.assertEqual(resultat["score"], Decimal("100.00"))

    def test_anomalie_retrait_si_tta_incorrecte(self):
        resultat = rapprocher_transaction(
            "RETRAIT",
            reference_partenaire="PIN1001",
            reference_amplitude="PIN1001",
            frais_retrait_partenaire=5000,
            tta_amplitude=90,
        )
        self.assertEqual(resultat["resultat"], "ANOMALIE")
        self.assertFalse(resultat["tta"])


class ConnexionTests(TestCase):

    def setUp(self):
        self.user = Utilisateur.objects.create_user(
            username="agentdemo",
            email="agent@bangecmr.com",
            password="MotDePasse123",
            role=Utilisateur.Roles.AGENT_ERA,
        )

    def test_connexion_par_email(self):
        response = self.client.post(
            reverse("connexion"),
            {"email": "agent@bangecmr.com", "password": "MotDePasse123"},
        )
        self.assertRedirects(response, reverse("dashboard"))

    def test_connexion_refusee(self):
        response = self.client.post(
            reverse("connexion"),
            {"email": "agent@bangecmr.com", "password": "mauvais"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "incorrect")

    def test_dashboard_apres_connexion(self):
        self.client.login(username="agentdemo", password="MotDePasse123")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tableau de bord")


class RapprochementIntegrationTests(TestCase):

    def setUp(self):
        self.user = Utilisateur.objects.create_user(
            username="agent",
            email="agent@bange.cm",
            password="x",
            role=Utilisateur.Roles.AGENT_ERA,
        )
        self.ria = SourceDonnees.objects.create(
            nom="RIA",
            type_source=SourceDonnees.TypeSource.PARTENAIRE,
        )
        self.amp = SourceDonnees.objects.create(
            nom="Amplitude",
            type_source=SourceDonnees.TypeSource.BANQUE,
        )
        self.yuba = SourceDonnees.objects.create(
            nom="YUBA",
            type_source=SourceDonnees.TypeSource.PARTENAIRE,
        )
    def _fichier(self, source, nom, contenu, type_operation=Transaction.TypeOperation.ENVOI):
        f = FichierImporte.objects.create(
            nom_fichier=nom,
            source=source,
            format_fichier="csv",
            type_operation=type_operation,
            importe_par=self.user,
            fichier=SimpleUploadedFile(nom, contenu, content_type="text/csv"),
        )
        resultat = importer_depuis_chemin(
            f.fichier.path,
            source.nom,
            fichier_importe=f,
            type_operation=type_operation,
        )
        self.assertTrue(resultat["ok"], resultat)
        return f
    def test_refuse_fichier_d_un_autre_partenaire(self):
        fp = FichierImporte.objects.create(
            nom_fichier="yuba.csv",
            source=self.yuba,
            format_fichier="csv",
            type_operation=Transaction.TypeOperation.ENVOI,
            importe_par=self.user,
            statut=FichierImporte.Statut.TRAITE,
        )
        fa = FichierImporte.objects.create(
            nom_fichier="amplitude.csv",
            source=self.amp,
            format_fichier="csv",
            type_operation=Transaction.TypeOperation.ENVOI,
            importe_par=self.user,
            statut=FichierImporte.Statut.TRAITE,
        )
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("lancer_rapprochement"),
            {
                "partenaire": self.ria.id,
                "type_operation": Transaction.TypeOperation.ENVOI,
                "fichier_partenaire": fp.id,
                "fichier_amplitude": fa.id,
            },
        )
        self.assertRedirects(response, reverse("lancer_rapprochement"))
        self.assertEqual(Rapprochement.objects.count(), 0)
    def test_cycle_complet_envoi(self):
        csv_p = (
            "reference;montant;date;nom_emetteur;nom_beneficiaire;customer_fee;tta;tva;cte;mttc\n"
            "RIA1001;100000;10/08/2026;a;b;2000;100;385;500;100985\n"
            "RIA1002;50000;10/08/2026;a;b;1500;50;200;100;50350\n"
            "RIA1003;75000;11/08/2026;a;b;1800;80;346.5;375;75801.5\n"
        ).encode("utf-8")
        csv_a = (
            "reference;montant;tva;tta;cte;mttc;dco;dev\n"
            "RIA1001;100000;385.00;100;500;100985.00;10/08/2026;XAF\n"
            "RIA1002;50000;288.75;50;250;50688.75;10/08/2026;XAF\n"
            "RIA1004;30000;100;40;150;30390;11/08/2026;XAF\n"
        ).encode("utf-8")

        fp = self._fichier(self.ria, "p.csv", csv_p)
        fa = self._fichier(self.amp, "a.csv", csv_a)
        r = lancer_rapprochement(
            self.user,
            self.ria,
            fp,
            fa,
            Transaction.TypeOperation.ENVOI,
        )
        correspondances = Correspondance.objects.filter(rapprochement=r)
        self.assertEqual(correspondances.count(), 2)
        self.assertEqual(correspondances.filter(automatique=True).count(), 1)
        self.assertEqual(correspondances.filter(automatique=False).count(), 1)
        a_verifier = correspondances.get(transaction_1__reference="RIA1002")
        self.assertEqual(a_verifier.score_correspondance, Decimal("90.00"))
        self.assertEqual(Anomalie.objects.filter(rapprochement=r).count(), 0)
        self.assertEqual(NonRapprochee.objects.filter(rapprochement=r).count(), 2)


    def test_cycle_complet_retrait(self):
        csv_p = (
            "pin;montant;date;frais_retrait\n"
            "PIN1001;10000;10/08/2026;5000\n"
        ).encode("utf-8")
        csv_a = (
            "reference;montant;tta;dco\n"
            "PIN1001;10000;100;10/08/2026\n"
        ).encode("utf-8")

        fp = self._fichier(
            self.ria,
            "retrait_partenaire.csv",
            csv_p,
            Transaction.TypeOperation.RETRAIT,
        )
        fa = self._fichier(
            self.amp,
            "retrait_amplitude.csv",
            csv_a,
            Transaction.TypeOperation.RETRAIT,
        )
        r = lancer_rapprochement(
            self.user,
            self.ria,
            fp,
            fa,
            Transaction.TypeOperation.RETRAIT,
        )
        self.assertEqual(Correspondance.objects.filter(rapprochement=r).count(), 1)
        self.assertEqual(Anomalie.objects.filter(rapprochement=r).count(), 0)
        self.assertEqual(NonRapprochee.objects.filter(rapprochement=r).count(), 0)

class PagesSmokeTests(TestCase):

    def setUp(self):
        self.user = Utilisateur.objects.create_user(
            username="agentpages",
            email="pages@bangecmr.com",
            password="MotDePasse123",
            role=Utilisateur.Roles.AGENT_ERA,
        )
        self.client.login(username="agentpages", password="MotDePasse123")

    def test_pages_principales(self):
        urls = [
            "importation",
            "liste_rapprochements",
            "lancer_rapprochement",
            "correspondances",
            "anomalies",
            "non_rapprochees",
            "liste_transactions",
        ]
        for name in urls:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)

        for name in ("rapports", "export_csv", "export_pdf"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302, name)


class ParcoursImportationEtRapprochementTests(TestCase):
    def setUp(self):
        self.user = Utilisateur.objects.create_user(
            username="agent-import",
            email="agent-import@bange.cm",
            password="MotDePasse123",
            role=Utilisateur.Roles.AGENT_ERA,
        )
        self.ria = SourceDonnees.objects.create(
            nom="RIA",
            type_source=SourceDonnees.TypeSource.PARTENAIRE,
        )
        SourceDonnees.objects.create(
            nom="Amplitude",
            type_source=SourceDonnees.TypeSource.BANQUE,
        )
        self.client.login(username="agent-import", password="MotDePasse123")

    def test_imports_depuis_formulaire_puis_rapprochement(self):
        fichier_partenaire = SimpleUploadedFile(
            "ria.csv",
            (
                "reference;montant;date;customer_fee;tta\n"
                "WEB1001;100000;24/09/2026;2000;100\n"
            ).encode("utf-8"),
            content_type="text/csv",
        )
        reponse = self.client.post(
            reverse("importation"),
            {
                "cote": "PARTENAIRE",
                "partenaire": self.ria.id,
                "type_operation": Transaction.TypeOperation.ENVOI,
                "fichier": fichier_partenaire,
            },
        )
        self.assertRedirects(reponse, reverse("importation"))
        partenaire = FichierImporte.objects.get(nom_fichier="ria.csv")
        self.assertEqual(partenaire.statut, FichierImporte.Statut.TRAITE)
        self.assertEqual(partenaire.nombre_transactions, 1)

        fichier_amplitude = SimpleUploadedFile(
            "amplitude.csv",
            (
                "reference;montant;tva;tta;cte;mttc;dco;dev\n"
                "WEB1001;100000;385;100;500;100985;24/09/2026;XAF\n"
            ).encode("utf-8"),
            content_type="text/csv",
        )
        reponse = self.client.post(
            reverse("importation"),
            {
                "cote": "AMPLITUDE",
                "partenaire": self.ria.id,
                "type_operation": Transaction.TypeOperation.ENVOI,
                "fichier": fichier_amplitude,
            },
        )
        self.assertRedirects(reponse, reverse("importation"))
        amplitude = FichierImporte.objects.get(nom_fichier="amplitude.csv")
        self.assertEqual(amplitude.statut, FichierImporte.Statut.TRAITE)

        reponse = self.client.post(
            reverse("lancer_rapprochement"),
            {
                "partenaire": self.ria.id,
                "type_operation": Transaction.TypeOperation.ENVOI,
                "fichier_partenaire": partenaire.id,
                "fichier_amplitude": amplitude.id,
            },
        )
        rapprochement = Rapprochement.objects.get(
            fichier_partenaire=partenaire,
            fichier_amplitude=amplitude,
        )
        self.assertRedirects(reponse, reverse("detail_rapprochement", args=[rapprochement.id]))
        self.assertEqual(rapprochement.nombre_correspondances, 1)
        self.assertEqual(rapprochement.nombre_anomalies, 0)


class ValidationMetierTests(TestCase):
    def setUp(self):
        self.responsable = Utilisateur.objects.create_user(
            username="responsable-validation",
            email="responsable-validation@bange.cm",
            password="MotDePasse123",
            role=Utilisateur.Roles.RESPONSABLE_ERA,
        )
        self.ria = SourceDonnees.objects.create(
            nom="RIA",
            type_source=SourceDonnees.TypeSource.PARTENAIRE,
        )
        amplitude = SourceDonnees.objects.create(
            nom="Amplitude",
            type_source=SourceDonnees.TypeSource.BANQUE,
        )
        partenaire_file = FichierImporte.objects.create(
            nom_fichier="ria.csv", source=self.ria, format_fichier="csv",
            type_operation=Transaction.TypeOperation.ENVOI,
            importe_par=self.responsable, statut=FichierImporte.Statut.TRAITE,
        )
        amplitude_file = FichierImporte.objects.create(
            nom_fichier="amplitude.csv", source=amplitude, format_fichier="csv",
            type_operation=Transaction.TypeOperation.ENVOI,
            importe_par=self.responsable, statut=FichierImporte.Statut.TRAITE,
        )
        transaction = Transaction.objects.create(
            reference="ANOM-001", source=self.ria, fichier_importe=partenaire_file,
            type_operation=Transaction.TypeOperation.ENVOI,
            date_transaction=timezone.now(), montant=1000,
        )
        self.rapprochement = Rapprochement.objects.create(
            lance_par=self.responsable, partenaire=self.ria,
            fichier_partenaire=partenaire_file, fichier_amplitude=amplitude_file,
            type_operation=Transaction.TypeOperation.ENVOI,
            statut=Rapprochement.Statut.TERMINE_AVEC_ANOMALIES,
            nombre_anomalies=1,
        )
        self.anomalie = Anomalie.objects.create(
            rapprochement=self.rapprochement, transaction=transaction,
            type_anomalie=Anomalie.TypeAnomalie.MONTANT,
            description="Écart de montant.",
        )
        self.client.force_login(self.responsable)

    def test_resoudre_anomalie_puis_valider_rapprochement(self):
        response = self.client.post(
            reverse("detail_anomalie", args=[self.anomalie.pk]),
            {"statut": Anomalie.Statut.RESOLUE},
        )
        self.assertRedirects(response, reverse("detail_anomalie", args=[self.anomalie.pk]))
        self.anomalie.refresh_from_db()
        self.assertEqual(self.anomalie.statut, Anomalie.Statut.RESOLUE)
        self.assertEqual(self.anomalie.resolue_par, self.responsable)
        self.assertIsNotNone(self.anomalie.date_resolution)

        response = self.client.post(
            reverse("valider_rapprochement", args=[self.rapprochement.pk])
        )
        self.assertRedirects(
            response, reverse("detail_rapprochement", args=[self.rapprochement.pk])
        )
        self.rapprochement.refresh_from_db()
        self.assertTrue(self.rapprochement.valide)
        self.assertEqual(self.rapprochement.valide_par, self.responsable)
