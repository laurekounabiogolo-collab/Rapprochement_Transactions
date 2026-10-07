import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from chatbot.models import Intention


class Command(BaseCommand):
    help = "Ajoute au chatbot le catalogue local d’intentions ERA."

    def handle(self, *args, **options):
        chemin = Path(__file__).resolve().parents[2] / "catalogue.jsonl"
        if not chemin.exists():
            raise CommandError("Le fichier chatbot/catalogue.jsonl est introuvable.")

        creees = 0
        enrichies = 0
        for numero, ligne in enumerate(chemin.read_text(encoding="utf-8").splitlines(), start=1):
            if not ligne.strip():
                continue
            try:
                item = json.loads(ligne)
            except json.JSONDecodeError as erreur:
                raise CommandError(f"Entrée {numero} du catalogue invalide : {erreur}") from erreur

            question = item["question"].strip()
            mots_cles = [mot.strip() for mot in item["mots_cles"] if mot.strip()]
            exemples = list(dict.fromkeys([
                question,
                *mots_cles,
                f"Peux-tu m’aider ? {question}",
                f"Je veux savoir {mots_cles[0]}" if mots_cles else question,
            ]))
            code = item["code"]
            intention = Intention.objects.filter(code=code).first()
            if intention is None:
                Intention.objects.create(
                    code=code,
                    nom=item["nom"],
                    exemples="\n".join(exemples),
                    reponse=item["reponse"],
                    active=True,
                )
                creees += 1
                continue

            existants = intention.obtenir_exemples()
            ajoutes = [exemple for exemple in exemples if exemple not in existants]
            if ajoutes:
                intention.exemples = "\n".join([*existants, *ajoutes])
                intention.save(update_fields=["exemples", "modifie_le"])
                enrichies += 1

        self.stdout.write(self.style.SUCCESS(
            f"Catalogue chargé : {creees} intentions créées, {enrichies} enrichies, "
            f"{Intention.objects.count()} intentions au total."
        ))
