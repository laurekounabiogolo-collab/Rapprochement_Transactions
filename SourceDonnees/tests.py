from django.test import TestCase
from django.urls import reverse

from SourceDonnees.forms import SourceDonneesForm
from importations.models import FichierImporte
from SourceDonnees.models import SourceDonnees
from utilisateurs.models import Utilisateur


class GestionSourcesTests(TestCase):
    def setUp(self):
        self.responsable = Utilisateur.objects.create_user(
            username="responsable-sources",
            email="responsable-sources@example.com",
            password="MotDePasse123",
            role=Utilisateur.Roles.RESPONSABLE_ERA,
        )
        self.agent = Utilisateur.objects.create_user(
            username="agent-sources",
            email="agent-sources@example.com",
            password="MotDePasse123",
            role=Utilisateur.Roles.AGENT_ERA,
        )

    def test_liste_reservee_aux_responsables(self):
        self.client.force_login(self.agent)
        response = self.client.get(reverse("liste_sources"))
        self.assertEqual(response.status_code, 302)
        self.client.force_login(self.responsable)
        response = self.client.get(reverse("liste_sources"))
        self.assertEqual(response.status_code, 200)

    def test_creation_source_partenaire(self):
        self.client.force_login(self.responsable)
        response = self.client.post(
            reverse("creer_source"),
            {
                "nom": "RIA",
                "type_source": SourceDonnees.TypeSource.PARTENAIRE,
                "description": "Partenaire de transfert",
                "actif": "on",
            },
        )
        self.assertRedirects(response, reverse("liste_sources"))
        self.assertTrue(
            SourceDonnees.objects.filter(
                nom="RIA",
                type_source=SourceDonnees.TypeSource.PARTENAIRE,
                actif=True,
            ).exists()
        )

    def test_amplitude_doit_etre_de_type_banque(self):
        form = SourceDonneesForm(
            data={
                "nom": "Amplitude",
                "type_source": SourceDonnees.TypeSource.PARTENAIRE,
                "description": "",
                "actif": "on",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("type_source", form.errors)

    def test_nom_unique_sans_tenir_compte_de_la_casse(self):
        SourceDonnees.objects.create(
            nom="RIA",
            type_source=SourceDonnees.TypeSource.PARTENAIRE,
        )
        form = SourceDonneesForm(
            data={
                "nom": "ria",
                "type_source": SourceDonnees.TypeSource.PARTENAIRE,
                "description": "",
                "actif": "on",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("nom", form.errors)

    def test_activation_et_desactivation_par_post(self):
        source = SourceDonnees.objects.create(
            nom="YUBA",
            type_source=SourceDonnees.TypeSource.PARTENAIRE,
            actif=True,
        )
        self.client.force_login(self.responsable)
        url = reverse("changer_statut_source", args=[source.pk])
        response = self.client.post(url)
        self.assertRedirects(response, reverse("liste_sources"))
        source.refresh_from_db()
        self.assertFalse(source.actif)
        self.client.post(url)
        source.refresh_from_db()
        self.assertTrue(source.actif)

    def test_type_source_ne_change_pas_apres_import(self):
        source = SourceDonnees.objects.create(
            nom="RIA",
            type_source=SourceDonnees.TypeSource.PARTENAIRE,
        )
        FichierImporte.objects.create(
            nom_fichier="ria.csv",
            source=source,
            format_fichier="csv",
            importe_par=self.responsable,
        )
        form = SourceDonneesForm(
            data={
                "nom": "RIA",
                "type_source": SourceDonnees.TypeSource.BANQUE,
                "description": "",
                "actif": "on",
            },
            instance=source,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("type_source", form.errors)

    def test_changement_de_nom_amplitude_refuse(self):
        source = SourceDonnees.objects.create(
            nom="Amplitude",
            type_source=SourceDonnees.TypeSource.BANQUE,
        )
        form = SourceDonneesForm(
            data={
                "nom": "Banque centrale",
                "type_source": SourceDonnees.TypeSource.BANQUE,
                "description": "",
                "actif": "on",
            },
            instance=source,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("nom", form.errors)
