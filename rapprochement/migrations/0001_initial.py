import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("SourceDonnees", "0001_initial"),
        ("importations", "0001_initial"),
        ("transactions", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Rapprochement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date_lancement", models.DateTimeField(auto_now_add=True)),
                ("statut", models.CharField(max_length=30, default="EN_COURS")),
                ("nombre_transactions", models.PositiveIntegerField(default=0)),
                ("nombre_correspondances", models.PositiveIntegerField(default=0)),
                ("nombre_anomalies", models.PositiveIntegerField(default=0)),
                (
                    "lance_par",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="rapprochements_lances",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Correspondance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("score_correspondance", models.DecimalField(decimal_places=2, max_digits=5)),
                ("automatique", models.BooleanField(default=True)),
                ("date_creation", models.DateTimeField(auto_now_add=True)),
                (
                    "rapprochement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="correspondances",
                        to="rapprochement.rapprochement",
                    ),
                ),
                (
                    "transaction_1",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="correspondances_1",
                        to="transactions.transaction",
                    ),
                ),
                (
                    "transaction_2",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="correspondances_2",
                        to="transactions.transaction",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Anomalie",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("type_anomalie", models.CharField(max_length=30)),
                ("description", models.TextField()),
                ("statut", models.CharField(max_length=20, default="NON_TRAITEE")),
                ("date_creation", models.DateTimeField(auto_now_add=True)),
                ("date_resolution", models.DateTimeField(blank=True, null=True)),
                (
                    "rapprochement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="anomalies",
                        to="rapprochement.rapprochement",
                    ),
                ),
                (
                    "transaction",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="anomalies",
                        to="transactions.transaction",
                    ),
                ),
                (
                    "resolue_par",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="anomalies_resolues",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
