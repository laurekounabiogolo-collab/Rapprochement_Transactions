import csv
from io import StringIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from SourceDonnees.models import SourceDonnees
from importations.models import FichierImporte
from importations.services import calculer_empreinte, importer_depuis_chemin
from transactions.models import Transaction
from utilisateurs.permissions import ROLES_AGENT, role_autorise


@login_required
@role_autorise(*ROLES_AGENT)
def telecharger_erreurs_import(request, pk):
    fichier = get_object_or_404(
        FichierImporte.objects.filter(importe_par=request.user).select_related("source"),
        pk=pk,
    )
    erreurs = [ligne for ligne in fichier.message_erreur.splitlines() if ligne.strip()]
    if not erreurs:
        messages.info(request, "Ce fichier ne contient aucune erreur d'import à télécharger.")
        return redirect("importation")

    contenu = StringIO()
    writer = csv.writer(contenu, delimiter=";")
    writer.writerow(["Fichier", fichier.nom_fichier])
    writer.writerow(["Source", fichier.source.nom])
    writer.writerow(["Type d'opération", fichier.type_operation or "Non renseigné"])
    writer.writerow([])
    writer.writerow(["Erreur"])
    for erreur in erreurs:
        writer.writerow([erreur])

    response = HttpResponse(
        "\ufeff" + contenu.getvalue(),
        content_type="text/csv; charset=utf-8",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="erreurs_import_{fichier.pk}.csv"'
    )
    return response


@login_required
@role_autorise(*ROLES_AGENT)
def importation(request):
    partenaires = SourceDonnees.objects.filter(
        actif=True,
        type_source=SourceDonnees.TypeSource.PARTENAIRE,
    ).order_by("nom")
    amplitude = SourceDonnees.objects.filter(
        nom="Amplitude",
        actif=True,
        type_source=SourceDonnees.TypeSource.BANQUE,
    ).first()
    types = Transaction.TypeOperation.choices

    if request.method == "POST":
        cote = request.POST.get("cote", "PARTENAIRE")
        type_operation = request.POST.get("type_operation")
        fichier = request.FILES.get("fichier")
        partenaire_id = request.POST.get("partenaire")

        if not fichier or not type_operation:
            messages.error(request, "Veuillez s\u00e9lectionner le type d\u0027op\u00e9ration et un fichier.")
            return redirect("importation")

        extension = fichier.name.rsplit(".", 1)[-1].lower() if "." in fichier.name else ""
        if extension not in {"csv", "xlsx", "xls"}:
            messages.error(request, "Format non pris en charge. Utilisez CSV (prioritaire) ou Excel.")
            return redirect("importation")

        contenu = fichier.read()
        empreinte = calculer_empreinte(contenu)
        fichier.seek(0)

        if cote == "AMPLITUDE":
            if not amplitude:
                messages.error(request, "La source Amplitude n'est pas configurée.")
                return redirect("importation")
            source = amplitude
            partenaire = SourceDonnees.objects.filter(pk=partenaire_id).first() if partenaire_id else None
        else:
            source = SourceDonnees.objects.filter(pk=partenaire_id).first()
            if not source:
                messages.error(request, "Veuillez choisir un partenaire.")
                return redirect("importation")
            partenaire = source

        doublon_fichier = FichierImporte.objects.filter(
            importe_par=request.user,
            source=source,
            empreinte=empreinte,
            type_operation=type_operation,
            statut=FichierImporte.Statut.TRAITE,
        ).exists()
        if doublon_fichier:
            messages.warning(
                request,
                "Ce fichier a déjà été importé pour cette source et ce type d'opération. "
                "Les transactions existantes n'ont pas été supprimées.",
            )
            return redirect("importation")

        enregistrement = FichierImporte(
            nom_fichier=fichier.name,
            source=source,
            format_fichier=extension[:10],
            type_operation=type_operation,
            empreinte=empreinte,
            importe_par=request.user,
            statut=FichierImporte.Statut.EN_ATTENTE,
        )
        enregistrement.fichier.save(fichier.name, ContentFile(contenu), save=True)

        resultat = importer_depuis_chemin(
            enregistrement.fichier.path,
            source.nom,
            fichier_importe=enregistrement,
            type_operation=type_operation,
                    utilisateur=request.user,
        )

        if not resultat.get("ok"):
            enregistrement.statut = FichierImporte.Statut.ERREUR
            enregistrement.message_erreur = resultat.get("message", "")
            enregistrement.save()
            messages.error(request, resultat.get("message", "Import impossible."))
            return redirect("importation")

        nb = len(resultat["creees"])
        enregistrement.nombre_transactions = nb
        enregistrement.statut = FichierImporte.Statut.TRAITE
        if resultat["erreurs"]:
            enregistrement.message_erreur = "\n".join(resultat["erreurs"])
        enregistrement.save()

        if cote == "AMPLITUDE":
            request.session["fichier_amplitude_id"] = enregistrement.id
            if partenaire:
                request.session["partenaire_id"] = partenaire.id
        else:
            request.session["fichier_partenaire_id"] = enregistrement.id
            request.session["partenaire_id"] = source.id
        request.session["type_operation"] = type_operation

        if nb or resultat["ignorees"]:
            messages.success(
                request,
                f"Importation r\u00e9ussie : {nb} transaction(s) enregistr\u00e9e(s), "
                f"{resultat['ignorees']} doublon(s) ignor\u00e9(s).",
            )
        else:
            messages.warning(
                request,
                "Import termin\u00e9, mais aucune transaction n\u0027a \u00e9t\u00e9 import\u00e9e. V\u00e9rifiez les erreurs ci-dessous.",
            )
        if resultat["erreurs"]:
            messages.warning(
                request,
                f"{len(resultat['erreurs'])} ligne(s) n\u0027ont pas pu \u00eatre import\u00e9es.",
            )
        return redirect("importation")

    fichiers = (
        FichierImporte.objects.filter(importe_par=request.user)
        .select_related("source", "importe_par")
        .order_by("-date_importation")[:20]
    )
    return render(
        request,
        "importations/importation.html",
        {
            "partenaires": partenaires,
            "types": types,
            "fichiers": fichiers,
            "peut_lancer": (
                FichierImporte.objects.filter(
                    importe_par=request.user,
                    statut=FichierImporte.Statut.TRAITE,
                    transactions__isnull=False,
                )
                .exclude(source__nom="Amplitude")
                .exists()
                and FichierImporte.objects.filter(
                    importe_par=request.user,
                    source__nom="Amplitude",
                    statut=FichierImporte.Statut.TRAITE,
                    transactions__isnull=False,
                ).exists()
            ),
            "session_partenaire": request.session.get("partenaire_id"),
            "session_type": request.session.get("type_operation"),
            "fichier_partenaire_id": request.session.get("fichier_partenaire_id"),
            "fichier_amplitude_id": request.session.get("fichier_amplitude_id"),
        },
    )
