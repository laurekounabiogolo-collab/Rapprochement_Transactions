from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from SourceDonnees.models import SourceDonnees
from transactions.forms import TransactionForm
from transactions.models import Transaction
from utilisateurs.permissions import ROLES_AGENT, role_autorise


@login_required
@role_autorise(*ROLES_AGENT)
def liste_transactions(request):
    qs = Transaction.objects.select_related("source", "fichier_importe").order_by(
        "-date_transaction"
    )
    reference = request.GET.get("reference", "").strip()
    partenaire = request.GET.get("partenaire", "")
    type_operation = request.GET.get("type_operation", "")
    statut = request.GET.get("statut", "")
    date_debut = request.GET.get("date_debut", "")
    date_fin = request.GET.get("date_fin", "")

    if reference:
        qs = qs.filter(Q(reference__icontains=reference) | Q(reference_externe__icontains=reference))
    if partenaire:
        qs = qs.filter(source_id=partenaire)
    if type_operation:
        qs = qs.filter(type_operation=type_operation)
    if statut:
        qs = qs.filter(statut=statut)
    if date_debut:
        qs = qs.filter(date_transaction__date__gte=date_debut)
    if date_fin:
        qs = qs.filter(date_transaction__date__lte=date_fin)

    return render(
        request,
        "transactions/liste.html",
        {
            "lignes": qs[:300],
            "total": qs.count(),
            "sources": SourceDonnees.objects.filter(actif=True),
            "types": Transaction.TypeOperation.choices,
            "statuts": Transaction.Statut.choices,
            "filtres": request.GET,
        },
    )


@login_required
@role_autorise(*ROLES_AGENT)
def modifier_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk)
    form = TransactionForm(request.POST or None, instance=transaction)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Transaction mise à jour.")
        return redirect("liste_transactions")
    return render(
        request,
        "transactions/formulaire.html",
        {"form": form, "transaction": transaction},
    )
