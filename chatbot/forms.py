from django import forms

from chatbot.models import Intention


class IntentionForm(forms.ModelForm):
    class Meta:
        model = Intention
        fields = ("code", "nom", "exemples", "reponse", "active")
        widgets = {
            "exemples": forms.Textarea(attrs={"rows": 10}),
            "reponse": forms.Textarea(attrs={"rows": 5}),
        }
        help_texts = {
            "exemples": "Saisis plusieurs formulations, une par ligne. Le modèle les associera à cette intention.",
            "reponse": "Cette réponse sera affichée lorsque le modèle reconnaîtra l’intention.",
        }
