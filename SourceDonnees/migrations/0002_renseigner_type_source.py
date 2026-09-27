from django.db import migrations


def renseigner_types(apps, schema_editor):
    SourceDonnees = apps.get_model("SourceDonnees", "SourceDonnees")
    SourceDonnees.objects.filter(nom="Amplitude").update(type_source="BANQUE")
    SourceDonnees.objects.exclude(nom="Amplitude").update(type_source="PARTENAIRE")


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("SourceDonnees", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(renseigner_types, noop),
    ]
