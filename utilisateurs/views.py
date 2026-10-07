from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models.deletion import ProtectedError
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from rapprochement.models import Anomalie, Correspondance, NonRapprochee, Rapprochement
from transactions.models import Transaction
from utilisateurs.models import Utilisateur
from utilisateurs.permissions import (
    ROLES_GESTION_COMPTES,
    peut_gerer_utilisateur,
    role_autorise,
)


def connexion(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        identifiant = (request.POST.get("email") or request.POST.get("username") or "").strip()
        password = request.POST.get("password")
        utilisateur = None

        if identifiant and password:
            try:
                compte = Utilisateur.objects.get(email__iexact=identifiant)
                utilisateur = authenticate(
                    request,
                    username=compte.username,
                    password=password,
                )
            except Utilisateur.DoesNotExist:
                utilisateur = authenticate(
                    request,
                    username=identifiant,
                    password=password,
                )

        if utilisateur is not None:
            login(request, utilisateur)
            return redirect("dashboard")

        messages.error(
            request,
            "Identifiant ou mot de passe incorrect.",
        )

    return render(request, "utilisateurs/connexion.html")


def deconnexion(request):
    logout(request)
    messages.success(request, "Vous avez été déconnecté.")
    return redirect("connexion")


@login_required
def dashboard(request):
    transactions_utilisateur = Transaction.objects.filter(fichier_importe__importe_par=request.user)
    rapprochements_utilisateur = Rapprochement.objects.filter(lance_par=request.user)
    total_tx = transactions_utilisateur.count()
    correspondances = Correspondance.objects.filter(rapprochement__in=rapprochements_utilisateur).count()
    anomalies = Anomalie.objects.filter(rapprochement__in=rapprochements_utilisateur).count()
    non_rapprochees = NonRapprochee.objects.filter(rapprochement__in=rapprochements_utilisateur).count()
    if non_rapprochees == 0:
        non_rapprochees = transactions_utilisateur.filter(
            statut=Transaction.Statut.NON_RAPPROCHEE
        ).count()

    par_partenaire = (
        transactions_utilisateur.exclude(source__nom="Amplitude")
        .values("source__nom")
        .annotate(total=Count("id"))
        .order_by("source__nom")
    )
    par_type = (
        transactions_utilisateur.exclude(type_operation__isnull=True)
        .exclude(type_operation="")
        .values("type_operation")
        .annotate(total=Count("id"))
        .order_by("type_operation")
    )
    rapprochements_recents = (
        rapprochements_utilisateur.select_related("partenaire", "lance_par")
        .order_by("-date_lancement")[:8]
    )

    return render(
        request,
        "utilisateurs/dashboard.html",
        {
            "total_tx": total_tx,
            "correspondances": correspondances,
            "anomalies": anomalies,
            "non_rapprochees": non_rapprochees,
            "par_partenaire": par_partenaire,
            "par_type": par_type,
            "rapprochements_recents": rapprochements_recents,
        },
    )


def _roles_possibles(acteur):
    if acteur.is_superuser or acteur.role == Utilisateur.Roles.DIRECTEUR_OMT:
        return list(Utilisateur.Roles.choices)
    return [(Utilisateur.Roles.AGENT_ERA, "Agent ERA")]


@login_required
@role_autorise(*ROLES_GESTION_COMPTES)
def liste_utilisateurs(request):
    qs = Utilisateur.objects.exclude(is_superuser=True).order_by("last_name", "username")
    if (
        not request.user.is_superuser
        and request.user.role == Utilisateur.Roles.RESPONSABLE_ERA
    ):
        qs = qs.filter(role=Utilisateur.Roles.AGENT_ERA)
    return render(request, "utilisateurs/liste.html", {"utilisateurs": qs})


@login_required
@role_autorise(*ROLES_GESTION_COMPTES)
def creer_utilisateur(request):
    if request.user.role == Utilisateur.Roles.AGENT_ERA:
        messages.error(request, "L'agent ERA ne peut pas créer de comptes utilisateurs.")
        return redirect("dashboard")

    roles_possibles = _roles_possibles(request.user)

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        role = request.POST.get("role")
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()

        if not peut_gerer_utilisateur(request.user, role_cible=role):
            messages.error(request, "Vous ne pouvez pas créer ce type de compte.")
            return redirect("liste_utilisateurs")

        if not username or not email or not password:
            messages.error(request, "Identifiant, email et mot de passe sont obligatoires.")
        elif Utilisateur.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur existe déjà.")
        elif Utilisateur.objects.filter(email__iexact=email).exists():
            messages.error(request, "Cet email est déjà utilisé.")
        else:
            Utilisateur.objects.create_user(
                username=username,
                email=email,
                password=password,
                role=role,
                first_name=first_name,
                last_name=last_name,
            )
            messages.success(request, "Utilisateur créé.")
            return redirect("liste_utilisateurs")

    return render(
        request,
        "utilisateurs/formulaire.html",
        {"roles_possibles": roles_possibles, "titre": "Nouvel utilisateur", "utilisateur": None},
    )


@login_required
@role_autorise(*ROLES_GESTION_COMPTES)
def modifier_utilisateur(request, pk):
    if request.user.role == Utilisateur.Roles.AGENT_ERA:
        messages.error(request, "L'agent ERA ne peut pas modifier de comptes.")
        return redirect("dashboard")

    cible = get_object_or_404(Utilisateur, pk=pk)
    if cible.is_superuser and not request.user.is_superuser:
        messages.error(request, "Ce compte ne peut pas être modifié.")
        return redirect("liste_utilisateurs")
    if not peut_gerer_utilisateur(request.user, cible=cible):
        messages.error(request, "Vous ne pouvez pas modifier cet utilisateur.")
        return redirect("liste_utilisateurs")

    roles_possibles = _roles_possibles(request.user)

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        role = request.POST.get("role")
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()

        if not peut_gerer_utilisateur(request.user, role_cible=role):
            messages.error(request, "Vous ne pouvez pas attribuer ce rôle.")
            return redirect("modifier_utilisateur", pk=pk)

        if not username or not email:
            messages.error(request, "Identifiant et email sont obligatoires.")
        elif Utilisateur.objects.exclude(pk=cible.pk).filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur existe déjà.")
        elif Utilisateur.objects.exclude(pk=cible.pk).filter(email__iexact=email).exists():
            messages.error(request, "Cet email est déjà utilisé.")
        else:
            cible.username = username
            cible.email = email
            cible.first_name = first_name
            cible.last_name = last_name
            cible.role = role
            if password:
                cible.set_password(password)
            cible.save()
            messages.success(request, "Utilisateur mis à jour.")
            return redirect("liste_utilisateurs")

    return render(
        request,
        "utilisateurs/formulaire.html",
        {
            "roles_possibles": roles_possibles,
            "titre": f"Modifier {cible.username}",
            "utilisateur": cible,
        },
    )


@login_required
@role_autorise(*ROLES_GESTION_COMPTES)
def desactiver_utilisateur(request, pk):
    if request.method != "POST":
        return redirect("liste_utilisateurs")
    cible = get_object_or_404(Utilisateur, pk=pk)
    if not peut_gerer_utilisateur(request.user, cible=cible):
        messages.error(request, "Action non autorisée.")
        return redirect("liste_utilisateurs")
    if cible == request.user:
        messages.error(request, "Vous ne pouvez pas désactiver votre propre compte.")
        return redirect("liste_utilisateurs")
    cible.is_active = not cible.is_active
    cible.save(update_fields=["is_active"])
    messages.success(request, "Statut du compte mis à jour.")
    return redirect("liste_utilisateurs")


@login_required
@role_autorise(*ROLES_GESTION_COMPTES)
def supprimer_utilisateur(request, pk):
    if request.method != "POST":
        return redirect("liste_utilisateurs")

    cible = get_object_or_404(Utilisateur, pk=pk)
    if cible == request.user:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        return redirect("liste_utilisateurs")
    if cible.is_superuser or not peut_gerer_utilisateur(request.user, cible=cible):
        messages.error(request, "Vous n'êtes pas autorisé à supprimer ce compte.")
        return redirect("liste_utilisateurs")

    nom = cible.username
    try:
        cible.delete()
    except ProtectedError:
        messages.error(
            request,
            "Ce compte est lié à des imports ou rapprochements historiques. "
            "Désactivez-le pour conserver l'historique.",
        )
    else:
        messages.success(request, f"Le compte {nom} a été supprimé.")
    return redirect("liste_utilisateurs")
