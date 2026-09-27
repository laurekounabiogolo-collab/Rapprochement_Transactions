import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("SourceDonnees", "0002_renseigner_type_source"),
        ("importations", "0002_fichierimporte_empreinte_and_more"),
        ("transactions", "0003_transaction_cte_recalculee_and_more"),
        ("rapprochement", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="rapprochement",
            name="partenaire",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="rapprochements",
                to="SourceDonnees.sourcedonnees",
            ),
        ),
        migrations.AddField(
            model_name="rapprochement",
            name="fichier_partenaire",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="rapprochements_partenaire",
                to="importations.fichierimporte",
            ),
        ),
        migrations.AddField(
            model_name="rapprochement",
            name="fichier_amplitude",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="rapprochements_amplitude",
                to="importations.fichierimporte",
            ),
        ),
        migrations.AddField(
            model_name="rapprochement",
            name="type_operation",
            field=models.CharField(
                choices=[
                    ("ENVOI", "Envoi"),
                    ("RETRAIT", "Retrait / Paiement"),
                    ("REMBOURSEMENT", "Remboursement"),
                ],
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="rapprochement",
            name="nombre_non_rapprochees",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="rapprochement",
            name="message",
            field=models.TextField(blank=True),
        ),
        migrations.CreateModel(
            name="NonRapprochee",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "cote",
                    models.CharField(
                        choices=[
                            ("PARTENAIRE", "Partenaire"),
                            ("AMPLITUDE", "Amplitude"),
                        ],
                        default="PARTENAIRE",
                        max_length=20,
                    ),
                ),
                ("description", models.TextField(blank=True)),
                ("date_creation", models.DateTimeField(auto_now_add=True)),
                (
                    "rapprochement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="non_rapprochees",
                        to="rapprochement.rapprochement",
                    ),
                ),
                (
                    "transaction",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="non_rapprochees",
                        to="transactions.transaction",
                    ),
                ),
            ],
        ),
    ]
