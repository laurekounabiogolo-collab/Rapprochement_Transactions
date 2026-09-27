from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("rapprochement", "0003_correspondance_date_validation_and_more")]
    operations = [
        migrations.AddField(
            model_name="anomalie",
            name="score",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name="nonrapprochee",
            name="score",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
    ]
