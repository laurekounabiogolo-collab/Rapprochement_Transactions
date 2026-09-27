from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class RapportsChartsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.directeur = User.objects.create_user(
            username="directeur_omt",
            email="directeur@bange.cm",
            password="secret123",
            role=User.Roles.DIRECTEUR_OMT,
        )

    def test_report_page_exposes_chart_data(self):
        self.client.force_login(self.directeur)
        response = self.client.get(reverse("rapports"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("chart_partenaire", response.context)
        self.assertIn("chart_type", response.context)
        self.assertIn("chart_statut", response.context)

    def test_exports_csv_et_pdf_pour_directeur(self):
        self.client.force_login(self.directeur)

        csv_response = self.client.get(reverse("export_csv"))
        self.assertEqual(csv_response.status_code, 200)
        self.assertEqual(csv_response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("attachment;", csv_response["Content-Disposition"])

        pdf_response = self.client.get(reverse("export_pdf"))
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response["Content-Type"], "application/pdf")
        self.assertTrue(pdf_response.content.startswith(b"%PDF"))
