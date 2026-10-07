from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from chatbot.forms import IntentionForm
from chatbot.models import Intention
from chatbot.services import predire_reponse
from utilisateurs.permissions import ROLES_GESTION_COMPTES, role_autorise


@login_required
def discuter(request):
    cle_historique = f"chatbot_historique_{request.user.pk}"
    historique = request.session.get(cle_historique, [])

    if request.method == "POST":
        question = (request.POST.get("question") or "").strip()
        intention_trouvee = ""
        if not question:
            reponse = "Écris une question pour commencer."
        elif len(question) > 500:
            reponse = "La question est trop longue. Limite-la à 500 caractères."
        else:
            intentions = list(Intention.objects.filter(active=True))
            try:
                code, reponse = predire_reponse(question, intentions)
                if code:
                    intention_trouvee = next((item.nom for item in intentions if item.code == code), "")
            except ValueError as erreur:
                reponse = str(erreur)
            except Exception:
                reponse = (
                    "Le modèle n’est pas disponible. Vérifie que scikit-learn est installé "
                    "et qu’au moins deux intentions actives contiennent des exemples."
                )

        if question:
            historique.append({
                "question": question,
                "reponse": reponse,
                "intention": intention_trouvee,
            })
            request.session[cle_historique] = historique[-100:]
        return redirect("chatbot")

    peut_gerer = request.user.is_superuser or request.user.role in ROLES_GESTION_COMPTES
    return render(request, "chatbot/discuter.html", {
        "historique": historique,
        "peut_gerer": peut_gerer,
    })


@login_required
@role_autorise(*ROLES_GESTION_COMPTES)
def liste_intentions(request):
    return render(request, "chatbot/intention_liste.html", {"intentions": Intention.objects.all()})


@login_required
@role_autorise(*ROLES_GESTION_COMPTES)
def creer_intention(request):
    form = IntentionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Intention enregistrée. Le modèle utilisera ses exemples.")
        return redirect("chatbot_intentions")
    return render(request, "chatbot/intention_formulaire.html", {"form": form, "titre": "Ajouter une intention"})


@login_required
@role_autorise(*ROLES_GESTION_COMPTES)
def modifier_intention(request, pk):
    intention = get_object_or_404(Intention, pk=pk)
    form = IntentionForm(request.POST or None, instance=intention)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Intention mise à jour. Le modèle utilisera ses exemples.")
        return redirect("chatbot_intentions")
    return render(request, "chatbot/intention_formulaire.html", {
        "form": form,
        "titre": f"Modifier : {intention.nom}",
    })
