from django.db import models


class Intention(models.Model):
    code = models.SlugField(max_length=60, unique=True, help_text="Identifiant stable, par exemple AIDE_IMPORTATION.")
    nom = models.CharField(max_length=120)
    exemples = models.TextField(help_text="Une question ou expression par ligne. Ce sont les exemples appris par le modèle.")
    reponse = models.TextField()
    active = models.BooleanField(default=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("nom",)

    def __str__(self):
        return self.nom

    def obtenir_exemples(self):
        return [ligne.strip() for ligne in self.exemples.splitlines() if ligne.strip()]
