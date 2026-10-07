from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from django.http import HttpResponseNotAllowed
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from importations.models import FichierImporte
from rapprochement.models import Anomalie, Correspondance, NonRapprochee, Rapprochement
from rapprochement.services import lancer_rapprochement
from SourceDonnees.models import SourceDonnees
from transactions.models import Transaction
from utilisateurs.permissions import (
    ROLES_AGENT,
    ROLES_CONSULTATION_RESULTATS,
    ROLES_RESPONSABLE,
    peut_traiter_anomalie,
    peut_valider_resultats,
    role_autorise,
)


@login_required
@role_autorise(*ROLES_CONSULTATION_RESULTATS)
def liste_rapprochements(request):
    qs = Rapprochement.objects.filter(lance_par=request.user).select_related("partenaire", "lance_par").order_by("-date_lancement")
    partenaire = request.GET.get("partenaire", "")
    type_operation = request.GET.get("type_operation", "")
    if partenaire:
        qs = qs.filter(partenaire_id=partenaire)
    if type_operation:
        qs = qs.filter(type_operation=type_operation)
    return render(
        request,
        "rapprochement/liste.html",
        {
            "rapprochements": qs,
            "partenaires": SourceDonnees.objects.filter(actif=True).exclude(nom="Amplitude"),
            "types": Transaction.TypeOperation.choices,
            "filtre_partenaire": partenaire,
            "filtre_type": type_operation,
            "peut_valider": peut_valider_resultats(request.user),
            "peut_supprimer": peut_valider_resultats(request.user),
        },
    )


@login_required
@role_autorise(*ROLES_RESPONSABLE)
def supprimer_rapprochement(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    rapprochement = get_object_or_404(Rapprochement.objects.filter(lance_par=request.user), pk=pk)
    identifiant = rapprochement.pk
    transaction_ids = set(rapprochement.correspondances.values_list("transaction_1_id", flat=True))
    transaction_ids.update(rapprochement.correspondances.values_list("transaction_2_id", flat=True))
    transaction_ids.update(rapprochement.anomalies.values_list("transaction_id", flat=True))
    transaction_ids.update(rapprochement.non_rapprochees.values_list("transaction_id", flat=True))
    with db_transaction.atomic():
        rapprochement.delete()
        for transaction in Transaction.objects.filter(pk__in=transaction_ids):
            a_un_autre_resultat = (
                transaction.correspondances_1.exists()
                or transaction.correspondances_2.exists()
                or transaction.anomalies.exists()
                or transaction.non_rapprochees.exists()
            )
            if not a_un_autre_resultat:
                transaction.statut = Transaction.Statut.EN_ATTENTE
                transaction.save(update_fields=["statut"])
    messages.success(
        request,
        f"Le rapprochement #{identifiant} et ses résultats associés ont été supprimés. "
        "Les transactions et fichiers importés sont conservés.",
    )
    return redirect("liste_rapprochements")


@login_required
@role_autorise(*ROLES_AGENT)
def lancer(request):
    partenaires = SourceDonnees.objects.filter(
        actif=True,
        type_source=SourceDonnees.TypeSource.PARTENAIRE,
    ).order_by("nom")

    if request.method == "POST":
        partenaire = get_object_or_404(partenaires, pk=request.POST.get("partenaire"))
        type_operation = request.POST.get("type_operation")
        fichiers_utilisateur = FichierImporte.objects.filter(importe_par=request.user)
        fp = get_object_or_404(fichiers_utilisateur, pk=request.POST.get("fichier_partenaire"))
        fa = get_object_or_404(fichiers_utilisateur, pk=request.POST.get("fichier_amplitude"))

        if type_operation not in dict(Transaction.TypeOperation.choices):
            messages.error(request, "Type d'opération invalide.")
            return redirect("lancer_rapprochement")
        if fp.source_id != partenaire.id:
            messages.error(request, "Le fichier partenaire sélectionné ne correspond pas au partenaire choisi.")
            return redirect("lancer_rapprochement")
        if (
            fa.source.nom != "Amplitude"
            or fa.source.type_source != SourceDonnees.TypeSource.BANQUE
            or not fa.source.actif
        ):
            messages.error(request, "Le second fichier doit provenir de la source Amplitude.")
            return redirect("lancer_rapprochement")
        if fp.statut != FichierImporte.Statut.TRAITE or fa.statut != FichierImporte.Statut.TRAITE:
            messages.error(request, "Les deux fichiers doivent avoir été importés avec succès.")
            return redirect("lancer_rapprochement")
        if fp.type_operation != type_operation or fa.type_operation != type_operation:
            messages.error(request, "Les deux fichiers doivent avoir le même type d'opération.")
            return redirect("lancer_rapprochement")
        if not fp.transactions.exists() or not fa.transactions.exists():
            messages.error(
                request,
                "Impossible de lancer le rapprochement : les deux fichiers "
                "doivent contenir des transactions import\u00e9es.",
            )
            return redirect("lancer_rapprochement")
        rapprochement = lancer_rapprochement(
            utilisateur=request.user,
            partenaire=partenaire,
            fichier_partenaire=fp,
            fichier_amplitude=fa,
            type_operation=type_operation,
        )
        if rapprochement.message:
            messages.warning(request, rapprochement.message)
        else:
            messages.success(request, f"Rapprochement #{rapprochement.id} terminé.")
        return redirect("detail_rapprochement", pk=rapprochement.pk)

    fichiers_p = list(
        FichierImporte.objects.filter(
            importe_par=request.user,
            source__type_source=SourceDonnees.TypeSource.PARTENAIRE,
            source__actif=True,
            statut=FichierImporte.Statut.TRAITE,
            transactions__isnull=False,
        )
        .distinct()
        .order_by("-date_importation")[:50]
    )
    fichiers_a = list(
        FichierImporte.objects.filter(
            importe_par=request.user,
            source__nom="Amplitude",
            source__type_source=SourceDonnees.TypeSource.BANQUE,
            source__actif=True,
            statut=FichierImporte.Statut.TRAITE,
            transactions__isnull=False,
        )
        .distinct()
        .order_by("-date_importation")[:50]
    )
    return render(
        request,
        "rapprochement/lancer.html",
        {
            "partenaires": partenaires,
            "types": Transaction.TypeOperation.choices,
            "fichiers_p": fichiers_p,
            "fichiers_a": fichiers_a,
            "partenaire_id": request.session.get("partenaire_id"),
            "type_operation": request.session.get("type_operation"),
            "fichier_partenaire_id": request.session.get("fichier_partenaire_id"),
            "fichier_amplitude_id": request.session.get("fichier_amplitude_id"),
        },
    )


@login_required
@role_autorise(*ROLES_CONSULTATION_RESULTATS)
def detail_rapprochement(request, pk):
    r = get_object_or_404(
        Rapprochement.objects.filter(lance_par=request.user).select_related("partenaire", "lance_par", "valide_par"),
        pk=pk,
    )
    return render(
        request,
        "rapprochement/detail.html",
        {
            "r": r,
            "peut_valider": peut_valider_resultats(request.user),
            "anomalies_ouvertes": r.anomalies.exclude(
                statut=Anomalie.Statut.RESOLUE
            ).count(),
        },
    )


@login_required
@role_autorise(*ROLES_RESPONSABLE)
def valider_rapprochement(request, pk):
    r = get_object_or_404(Rapprochement.objects.filter(lance_par=request.user), pk=pk)
    if request.method != "POST" or not peut_valider_resultats(request.user):
        messages.error(
            request,
            "Seul le Responsable ERA ou le Directeur OMT peut valider ce rapprochement.",
        )
        return redirect("detail_rapprochement", pk=pk)
    if r.valide:
        messages.info(request, "Ce rapprochement est déjà validé.")
        return redirect("detail_rapprochement", pk=pk)
    ouvertes = r.anomalies.exclude(statut=Anomalie.Statut.RESOLUE).count()
    if ouvertes:
        messages.error(
            request,
            f"Impossible de valider : {ouvertes} anomalie(s) restent à traiter.",
        )
        return redirect("detail_rapprochement", pk=pk)
    r.valide = True
    r.valide_par = request.user
    r.date_validation = timezone.now()
    r.save(update_fields=["valide", "valide_par", "date_validation"])
    messages.success(request, f"Rapprochement #{r.id} validé.")
    return redirect("detail_rapprochement", pk=pk)


@login_required
@role_autorise(*ROLES_CONSULTATION_RESULTATS)
def correspondances(request):
    qs = Correspondance.objects.filter(rapprochement__lance_par=request.user).select_related(
        "rapprochement",
        "rapprochement__partenaire",
        "transaction_1",
        "transaction_2",
        "validee_par",
    ).order_by("-date_creation")
    reference = request.GET.get("reference", "").strip()
    partenaire = request.GET.get("partenaire", "")
    type_operation = request.GET.get("type_operation", "")
    date_debut = request.GET.get("date_debut", "")
    if reference:
        qs = qs.filter(
            Q(transaction_1__reference__icontains=reference)
            | Q(transaction_2__reference__icontains=reference)
        )
    if partenaire:
        qs = qs.filter(rapprochement__partenaire_id=partenaire)
    if type_operation:
        qs = qs.filter(rapprochement__type_operation=type_operation)
    if date_debut:
        qs = qs.filter(transaction_1__date_transaction__date__gte=date_debut)
    return render(
        request,
        "rapprochement/correspondances.html",
        {
            "lignes": qs[:200],
            "partenaires": SourceDonnees.objects.filter(actif=True).exclude(nom="Amplitude"),
            "types": Transaction.TypeOperation.choices,
            "filtres": request.GET,
            "peut_valider": peut_valider_resultats(request.user),
        },
    )


@login_required
@role_autorise(*ROLES_RESPONSABLE)
def valider_correspondance(request, pk):
    if request.method != "POST" or not peut_valider_resultats(request.user):
        messages.error(
            request,
            "Seul le Responsable ERA ou le Directeur OMT peut valider une correspondance.",
        )
        return redirect("correspondances")
    c = get_object_or_404(Correspondance.objects.filter(rapprochement__lance_par=request.user), pk=pk)
    if c.validee:
        messages.info(request, "Cette correspondance est déjà validée.")
        return redirect("correspondances")
    c.validee = True
    c.validee_par = request.user
    c.date_validation = timezone.now()
    c.save(update_fields=["validee", "validee_par", "date_validation"])
    messages.success(request, f"Correspondance {c.transaction_1.reference} validée.")
    return redirect("correspondances")


@login_required
@role_autorise(*ROLES_CONSULTATION_RESULTATS)
def anomalies(request):
    qs = Anomalie.objects.filter(rapprochement__lance_par=request.user).select_related(
        "rapprochement",
        "rapprochement__partenaire",
        "transaction",
        "resolue_par",
    ).order_by("-date_creation")
    reference = request.GET.get("reference", "").strip()
    partenaire = request.GET.get("partenaire", "")
    type_operation = request.GET.get("type_operation", "")
    statut = request.GET.get("statut", "")
    if reference:
        qs = qs.filter(transaction__reference__icontains=reference)
    if partenaire:
        qs = qs.filter(rapprochement__partenaire_id=partenaire)
    if type_operation:
        qs = qs.filter(rapprochement__type_operation=type_operation)
    if statut:
        qs = qs.filter(statut=statut)
    return render(
        request,
        "rapprochement/anomalies.html",
        {
            "lignes": qs[:200],
            "partenaires": SourceDonnees.objects.filter(actif=True).exclude(nom="Amplitude"),
            "types": Transaction.TypeOperation.choices,
            "statuts": Anomalie.Statut.choices,
            "filtres": request.GET,
            "peut_traiter": peut_traiter_anomalie(request.user),
        },
    )


@login_required
@role_autorise(*ROLES_CONSULTATION_RESULTATS)
def detail_anomalie(request, pk):

    try:
        a = get_object_or_404(
            Anomalie.objects.filter(rapprochement__lance_par=request.user).select_related(
                "rapprochement",
                "transaction",
                "transaction__source",
                "resolue_par",
            ),
            pk=pk,
        )
        peut_traiter = peut_traiter_anomalie(request.user)
        if request.method == "POST":
            if not peut_traiter:
                messages.error(
                    request,
                    "L'agent ERA peut uniquement consulter les anomalies. "
                    "Le traitement est réservé au Responsable ERA ou au Directeur OMT.",
                )
                return redirect("detail_anomalie", pk=pk)
            nouveau = request.POST.get("statut")
            if nouveau in dict(Anomalie.Statut.choices):
                a.statut = nouveau
                if nouveau == Anomalie.Statut.RESOLUE:
                    a.resolue_par = request.user
                    a.date_resolution = timezone.now()
                else:
                    a.resolue_par = None
                    a.date_resolution = None
                a.save(update_fields=["statut", "resolue_par", "date_resolution"])
                messages.success(request, "Anomalie mise à jour.")
                return redirect("detail_anomalie", pk=pk)
        return render(
            request,
            "rapprochement/anomalie_detail.html",
            {"a": a, "peut_traiter": peut_traiter, "statuts": Anomalie.Statut.choices},
        )
    except Exception as e :
        print(e)


@login_required
@role_autorise(*ROLES_CONSULTATION_RESULTATS)
def non_rapprochees(request):
    qs = NonRapprochee.objects.filter(rapprochement__lance_par=request.user).select_related(
        "rapprochement",
        "rapprochement__partenaire",
        "transaction",
        "transaction__source",
    ).order_by("-date_creation")
    reference = request.GET.get("reference", "").strip()
    partenaire = request.GET.get("partenaire", "")
    type_operation = request.GET.get("type_operation", "")
    if reference:
        qs = qs.filter(transaction__reference__icontains=reference)
    if partenaire:
        qs = qs.filter(rapprochement__partenaire_id=partenaire)
    if type_operation:
        qs = qs.filter(rapprochement__type_operation=type_operation)
    return render(
        request,
        "rapprochement/non_rapprochees.html",
        {
            "lignes": qs[:200],
            "partenaires": SourceDonnees.objects.filter(actif=True).exclude(nom="Amplitude"),
            "types": Transaction.TypeOperation.choices,
            "filtres": request.GET,
        },
    )
