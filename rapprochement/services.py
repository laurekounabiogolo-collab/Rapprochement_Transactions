from django.db import transaction as db_transaction

from rapprochement.matching import determiner_anomalie, rapprocher_transactions_base
from rapprochement.models import Anomalie, Correspondance, NonRapprochee, Rapprochement
from transactions.models import Transaction


def lancer_rapprochement(
    utilisateur,
    partenaire,
    fichier_partenaire,
    fichier_amplitude,
    type_operation,
):
    """
    Exécute le moteur existant et enregistre les résultats.
    """

    transactions_partenaire = list(
        Transaction.objects.filter(fichier_importe=fichier_partenaire)
    )
    transactions_amplitude = list(
        Transaction.objects.filter(fichier_importe=fichier_amplitude)
    )

    resultat = rapprocher_transactions_base(
        transactions_partenaire,
        transactions_amplitude,
        type_operation,
    )

    with db_transaction.atomic():
        rapprochement = Rapprochement.objects.create(
            lance_par=utilisateur,
            partenaire=partenaire,
            fichier_partenaire=fichier_partenaire,
            fichier_amplitude=fichier_amplitude,
            type_operation=type_operation,
            statut=Rapprochement.Statut.EN_COURS,
            nombre_transactions=len(transactions_partenaire),
        )

        for item in resultat["correspondances"]:
            Correspondance.objects.create(
                rapprochement=rapprochement,
                transaction_1=item["partenaire"],
                transaction_2=item["amplitude"],
                score_correspondance=item["details"].get("score", 0),
                automatique=item["details"].get("automatique", True),
            )
            item["partenaire"].statut = Transaction.Statut.RAPPROCHEE
            item["partenaire"].save(update_fields=["statut"])
            item["amplitude"].statut = Transaction.Statut.RAPPROCHEE
            item["amplitude"].save(update_fields=["statut"])

        for item in resultat["anomalies"]:
            details = item["details"]
            info = determiner_anomalie(details) or {
                "type": "MTTC",
                "description": "Écart détecté entre partenaire et Amplitude.",
            }
            if details.get("ecart_mttc"):
                info["description"] += f" Écart MTTC : {details['ecart_mttc']}."

            Anomalie.objects.create(
                rapprochement=rapprochement,
                transaction=item["partenaire"],
                type_anomalie=info["type"],
                description=info["description"],
                score=details.get("score", 0),
            )
            item["partenaire"].statut = Transaction.Statut.ANOMALIE
            item["partenaire"].save(update_fields=["statut"])
            item["amplitude"].statut = Transaction.Statut.ANOMALIE
            item["amplitude"].save(update_fields=["statut"])

        for item in resultat["non_rapprochees"]:
            tx = item["transaction"]
            NonRapprochee.objects.create(
                rapprochement=rapprochement,
                transaction=tx,
                cote=item.get("cote", NonRapprochee.Cote.PARTENAIRE),
                description=item.get("description", ""),
                score=item.get("details", {}).get("score", 0),
            )
            tx.statut = Transaction.Statut.NON_RAPPROCHEE
            tx.save(update_fields=["statut"])

        rapprochement.nombre_correspondances = rapprochement.correspondances.count()
        rapprochement.nombre_anomalies = rapprochement.anomalies.count()
        rapprochement.nombre_non_rapprochees = rapprochement.non_rapprochees.count()
        if rapprochement.nombre_anomalies:
            rapprochement.statut = Rapprochement.Statut.TERMINE_AVEC_ANOMALIES
        else:
            rapprochement.statut = Rapprochement.Statut.TERMINE
        rapprochement.save()

    return rapprochement
