from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from utilisateurs.permissions import peut_gerer_utilisateur


class RolePermissionsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.agent = User.objects.create_user(
            username="agent_era",
            email="agent@bange.cm",
            password="secret123",
            role=User.Roles.AGENT_ERA,
        )
        self.responsable = User.objects.create_user(
            username="responsable_era",
            email="responsable@bange.cm",
            password="secret123",
            role=User.Roles.RESPONSABLE_ERA,
        )
        self.directeur = User.objects.create_user(
            username="directeur_omt",
            email="directeur@bange.cm",
            password="secret123",
            role=User.Roles.DIRECTEUR_OMT,
        )

    def test_agent_era_ne_peut_pas_gerer_des_comptes(self):
        self.assertFalse(peut_gerer_utilisateur(self.agent, role_cible="AGENT_ERA"))
        self.assertFalse(peut_gerer_utilisateur(self.agent, role_cible="RESPONSABLE_ERA"))
        self.assertFalse(peut_gerer_utilisateur(self.agent, role_cible="DIRECTEUR_OMT"))

    def test_responsable_era_ne_gerer_que_les_agents(self):
        self.assertTrue(peut_gerer_utilisateur(self.responsable, role_cible="AGENT_ERA"))
        self.assertFalse(peut_gerer_utilisateur(self.responsable, role_cible="RESPONSABLE_ERA"))
        self.assertFalse(peut_gerer_utilisateur(self.responsable, role_cible="DIRECTEUR_OMT"))

    def test_directeur_omt_gerer_tous_les_comptes(self):
        self.assertTrue(peut_gerer_utilisateur(self.directeur, role_cible="AGENT_ERA"))
        self.assertTrue(peut_gerer_utilisateur(self.directeur, role_cible="RESPONSABLE_ERA"))
        self.assertTrue(peut_gerer_utilisateur(self.directeur, role_cible="DIRECTEUR_OMT"))

    def test_agent_era_ne_peut_pas_acceder_au_formulaire_creation(self):
        self.client.force_login(self.agent)
        response = self.client.get(reverse("creer_utilisateur"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("dashboard"))

    def test_responsable_era_peut_creer_des_agents(self):
        self.client.force_login(self.responsable)
        response = self.client.get(reverse("creer_utilisateur"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Agent ERA")
