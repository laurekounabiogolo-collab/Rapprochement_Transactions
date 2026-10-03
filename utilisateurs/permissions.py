from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from utilisateurs.models import Utilisateur


ROLES_AGENT = (
    Utilisateur.Roles.AGENT_ERA,
    Utilisateur.Roles.RESPONSABLE_ERA,
)

ROLES_RESPONSABLE = (
    Utilisateur.Roles.RESPONSABLE_ERA,
    Utilisateur.Roles.DIRECTEUR_OMT,
)
ROLES_DIRECTEUR = (Utilisateur.Roles.DIRECTEUR_OMT,)
ROLES_CONSULTATION_RESULTATS = (*ROLES_AGENT, *ROLES_DIRECTEUR)
ROLES_GESTION_COMPTES = (
    Utilisateur.Roles.RESPONSABLE_ERA,
    Utilisateur.Roles.DIRECTEUR_OMT,
)
ROLES_GESTION_SOURCES = (Utilisateur.Roles.DIRECTEUR_OMT,)
ROLES_RAPPORTS = ROLES_RESPONSABLE


def role_autorise(*roles):
    def decorator(vue):
        @wraps(vue)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("connexion")
            if request.user.is_superuser and request.user.role not in (Utilisateur.Roles.AGENT_ERA, Utilisateur.Roles.RESPONSABLE_ERA):
                return vue(request, *args, **kwargs)
            if request.user.role not in roles:
                messages.error(
                    request,
                    "Vous n'avez pas les droits nécessaires pour cette action.",
                )
                return redirect("dashboard")
            return vue(request, *args, **kwargs)

        return wrapper

    return decorator


def est_responsable_metier(utilisateur):
    """Check approval roles; the Agent role never receives supervisor rights."""
    role = getattr(utilisateur, "role", None)
    if role == Utilisateur.Roles.AGENT_ERA:
        return False
    return bool(
        getattr(utilisateur, "is_superuser", False)
        or role in ROLES_RESPONSABLE
    )

def peut_traiter_anomalie(utilisateur):
    """L'agent ERA consulte seulement. Le traitement suit le rôle métier."""
    return est_responsable_metier(utilisateur)


def peut_valider_resultats(utilisateur):
    return est_responsable_metier(utilisateur)


def peut_generer_pdf(utilisateur):
    return est_responsable_metier(utilisateur)


def peut_gerer_utilisateur(acteur, cible=None, role_cible=None):
    if acteur.role == Utilisateur.Roles.AGENT_ERA:
        return False

    if acteur.is_superuser:
        return True

    if acteur.role == Utilisateur.Roles.DIRECTEUR_OMT:
        return True

    if acteur.role != Utilisateur.Roles.RESPONSABLE_ERA:
        return False

    role = role_cible or (cible.role if cible else None)
    return role == Utilisateur.Roles.AGENT_ERA
