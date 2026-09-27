import csv
from io import StringIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from rapprochement.models import Anomalie, Correspondance, NonRapprochee, Rapprochement
from rapports.pdf_utils import generer_pdf_rapport
from SourceDonnees.models import SourceDonnees
from transactions.models import Transaction
from utilisateurs.permissions import ROLES_RAPPORTS, peut_generer_pdf, role_autorise


def _statistiques(date_debut=None, date_fin=None, partenaire_id=None):
    tx = Transaction.objects.all()
    rapp = Rapprochement.objects.all()
    if date_debut:
        tx = tx.filter(date_transaction__date__gte=date_debut)
        rapp = rapp.filter(date_lancement__date__gte=date_debut)
    if date_fin:
        tx = tx.filter(date_transaction__date__lte=date_fin)
        rapp = rapp.filter(date_lancement__date__lte=date_fin)
    if partenaire_id:
        tx = tx.filter(source_id=partenaire_id)
        rapp = rapp.filter(partenaire_id=partenaire_id)

    stats = {
        "total_tx": tx.count(),
        "correspondances": Correspondance.objects.filter(rapprochement__in=rapp).count()
        if (date_debut or date_fin or partenaire_id)
        else Correspondance.objects.count(),
        "anomalies": Anomalie.objects.filter(rapprochement__in=rapp).count()
        if (date_debut or date_fin or partenaire_id)
        else Anomalie.objects.count(),
        "non_rapprochees": NonRapprochee.objects.filter(rapprochement__in=rapp).count()
        if (date_debut or date_fin or partenaire_id)
        else NonRapprochee.objects.count(),
        "par_partenaire": tx.exclude(source__nom="Amplitude")
        .values("source__nom")
        .annotate(total=Count("id"))
        .order_by("source__nom"),
        "par_type": tx.exclude(type_operation__isnull=True)
        .exclude(type_operation="")
        .values("type_operation")
        .annotate(total=Count("id"))
        .order_by("type_operation"),
        "rapprochements": rapp.select_related("partenaire").order_by("-date_lancement")[:30],
    }

    stats["chart_partenaire"] = [
        {"label": entry["source__nom"], "value": entry["total"]}
        for entry in stats["par_partenaire"]
    ]
    stats["chart_type"] = [
        {"label": entry["type_operation"], "value": entry["total"]}
        for entry in stats["par_type"]
    ]
    stats["chart_statut"] = [
        {"label": "Correspondances", "value": stats["correspondances"]},
        {"label": "Anomalies", "value": stats["anomalies"]},
        {"label": "Non rapprochées", "value": stats["non_rapprochees"]},
    ]
    return stats


@login_required
@role_autorise(*ROLES_RAPPORTS)
def rapports(request):
    date_debut = request.GET.get("date_debut") or None
    date_fin = request.GET.get("date_fin") or None
    partenaire_id = request.GET.get("partenaire") or None
    stats = _statistiques(date_debut, date_fin, partenaire_id)
    return render(
        request,
        "rapports/rapports.html",
        {
            "stats": stats,
            "chart_partenaire": stats["chart_partenaire"],
            "chart_type": stats["chart_type"],
            "chart_statut": stats["chart_statut"],
            "partenaires": SourceDonnees.objects.filter(actif=True).exclude(nom="Amplitude"),
            "filtres": request.GET,
            "peut_pdf": peut_generer_pdf(request.user),
        },
    )


@login_required
@role_autorise(*ROLES_RAPPORTS)
def export_csv(request):
    date_debut = request.GET.get("date_debut") or None
    date_fin = request.GET.get("date_fin") or None
    partenaire_id = request.GET.get("partenaire") or None
    stats = _statistiques(date_debut, date_fin, partenaire_id)

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(["Rapport de rapprochement ERA - BANGE Bank Cameroun"])
    writer.writerow(["Date generation", timezone.now().strftime("%d/%m/%Y %H:%M")])
    writer.writerow([])
    writer.writerow(["Indicateur", "Valeur"])
    writer.writerow(["Transactions", stats["total_tx"]])
    writer.writerow(["Correspondances", stats["correspondances"]])
    writer.writerow(["Anomalies", stats["anomalies"]])
    writer.writerow(["Non rapprochees", stats["non_rapprochees"]])
    writer.writerow([])
    writer.writerow(["Partenaire", "Nombre"])
    for ligne in stats["par_partenaire"]:
        writer.writerow([ligne["source__nom"], ligne["total"]])
    writer.writerow([])
    writer.writerow(["Type operation", "Nombre"])
    for ligne in stats["par_type"]:
        writer.writerow([ligne["type_operation"], ligne["total"]])

    response = HttpResponse(buffer.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="rapport_rapprochement.csv"'
    return response


@login_required
@role_autorise(*ROLES_RAPPORTS)
def export_pdf(request):
    if not peut_generer_pdf(request.user):
        messages.error(
            request,
            "La génération du rapport PDF est réservée au responsable ERA.",
        )
        return redirect("rapports")

    date_debut = request.GET.get("date_debut") or None
    date_fin = request.GET.get("date_fin") or None
    partenaire_id = request.GET.get("partenaire") or None
    stats = _statistiques(date_debut, date_fin, partenaire_id)
    auteur = request.user.get_full_name() or request.user.username
    contenu = generer_pdf_rapport(stats, date_debut, date_fin, auteur)
    response = HttpResponse(contenu, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="rapport_rapprochement_ERA.pdf"'
    return response
