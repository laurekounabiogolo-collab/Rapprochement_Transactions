from django import forms

from transactions.models import Transaction


class TransactionForm(forms.ModelForm):
    date_transaction = forms.DateTimeField(
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"},
            format="%Y-%m-%dT%H:%M",
        ),
    )

    class Meta:
        model = Transaction
        fields = [
            "reference",
            "source",
            "type_operation",
            "date_transaction",
            "montant",
            "devise",
            "reference_externe",
            "nom_emetteur",
            "nom_beneficiaire",
            "statut",
        ]
        widgets = {
            "montant": forms.NumberInput(attrs={"step": "0.01"}),
        }
