from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from SourceDonnees.forms import SourceDonneesForm
from SourceDonnees.models import SourceDonnees
from utilisateurs.permissions import ROLES_GESTION_SOURCES, role_autorise


@login_required
@role_autorise(*ROLES_GESTION_SOURCES)
def liste_sources(request):
    sources = SourceDonnees.objects.annotate(
        fichiers_count=Count(
            "fichiers",
            filter=Q(fichiers__importe_par=request.user),
            distinct=True,
        ),
        transactions_count=Count(
            "transactions",
            filter=Q(transactions__fichier_importe__importe_par=request.user),
            distinct=True,
        ),
    ).order_by("nom")

    recherche = request.GET.get("q", "").strip()
    type_source = request.GET.get("type_source", "")
    actif = request.GET.get("actif", "")

    if recherche:
        sources = sources.filter(
            Q(nom__icontains=recherche) | Q(description__icontains=recherche)
        )
    if type_source in dict(SourceDonnees.TypeSource.choices):
        sources = sources.filter(type_source=type_source)
    if actif in {"oui", "non"}:
        sources = sources.filter(actif=(actif == "oui"))

    return render(
        request,
        "SourceDonnees/liste.html",
        {
            "sources": sources,
            "types": SourceDonnees.TypeSource.choices,
            "filtres": request.GET,
        },
    )


@login_required
@role_autorise(*ROLES_GESTION_SOURCES)
def creer_source(request):
    form = SourceDonneesForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        source = form.save()
        messages.success(request, f"Source {source.nom} cr\u00e9\u00e9e.")
        return redirect("liste_sources")
    return render(
        request,
        "SourceDonnees/formulaire.html",
        {"form": form, "titre": "Nouvelle source"},
    )


@login_required
@role_autorise(*ROLES_GESTION_SOURCES)
def modifier_source(request, pk):
    source = get_object_or_404(SourceDonnees, pk=pk)
    form = SourceDonneesForm(request.POST or None, instance=source)
    if request.method == "POST" and form.is_valid():
        source = form.save()
        messages.success(request, f"Source {source.nom} mise \u00e0 jour.")
        return redirect("liste_sources")
    return render(
        request,
        "SourceDonnees/formulaire.html",
        {"form": form, "titre": f"Modifier {source.nom}", "source": source},
    )


@login_required
@role_autorise(*ROLES_GESTION_SOURCES)
def changer_statut_source(request, pk):
    if request.method != "POST":
        return redirect("liste_sources")
    source = get_object_or_404(SourceDonnees, pk=pk)
    source.actif = not source.actif
    source.save(update_fields=["actif"])
    statut = "activ\u00e9e" if source.actif else "d\u00e9sactiv\u00e9e"
    messages.success(request, f"Source {source.nom} {statut}.")
    return redirect("liste_sources")
