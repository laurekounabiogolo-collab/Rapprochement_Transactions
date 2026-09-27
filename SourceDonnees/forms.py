from django import forms

from SourceDonnees.models import SourceDonnees


class SourceDonneesForm(forms.ModelForm):
    class Meta:
        model = SourceDonnees
        fields = ["nom", "type_source", "description", "actif"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def clean_nom(self):
        nom = self.cleaned_data["nom"].strip()
        sources = SourceDonnees.objects.filter(nom__iexact=nom)
        if self.instance.pk:
            sources = sources.exclude(pk=self.instance.pk)
        if sources.exists():
            raise forms.ValidationError("Une source porte d\u00e9j\u00e0 ce nom.")
        if (
            self.instance.pk
            and self.instance.nom.casefold() == "amplitude"
            and nom.casefold() != "amplitude"
        ):
            raise forms.ValidationError(
                "Le nom technique de la source Amplitude ne peut pas \u00eatre modifi\u00e9."
            )
        if nom.casefold() == "amplitude":
            return "Amplitude"
        return nom

    def clean(self):
        cleaned_data = super().clean()
        nom = (cleaned_data.get("nom") or "").strip()
        type_source = cleaned_data.get("type_source")
        if (
            self.instance.pk
            and type_source != self.instance.type_source
            and (
                self.instance.fichiers.exists()
                or self.instance.transactions.exists()
            )
        ):
            self.add_error(
                "type_source",
                "Le type ne peut pas etre modifie apres l'import de donnees.",
            )
        if nom.casefold() == "amplitude" and type_source != SourceDonnees.TypeSource.BANQUE:
            self.add_error(
                "type_source",
                "Amplitude doit \u00eatre enregistr\u00e9e comme source bancaire.",
            )
        return cleaned_data
