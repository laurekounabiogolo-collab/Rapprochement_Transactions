from decimal import Decimal, InvalidOperation


POIDS_SCORE = {
    "ENVOI": {
        "reference": Decimal("40"),
        "montant": Decimal("20"),
        "tva": Decimal("10"),
        "tta": Decimal("10"),
        "cte": Decimal("10"),
        "mttc": Decimal("10"),
    },
    "REMBOURSEMENT": {
        "reference": Decimal("50"),
        "mttc": Decimal("50"),
    },
    "RETRAIT": {
        "reference": Decimal("50"),
        "tta": Decimal("50"),
    },
}

TOLERANCES_MONTANTS = {"defaut": Decimal("0.00")}
SEUILS_SCORE = {"automatique": Decimal("100"), "a_verifier": Decimal("80"), "anomalie": Decimal("50")}


def calculer_score(resultat, type_operation):
    """Calcule un score sur 100 à partir des critères comparés."""
    poids = POIDS_SCORE.get(type_operation, {})
    score = sum(
        (
            poids.get(critere, Decimal("0"))
            for critere, valide in resultat.items()
            if valide is True
        ),
        Decimal("0"),
    )
    return score.quantize(Decimal("0.01"))


def comparer_valeurs(valeur1, valeur2):
    """
    Compare deux valeurs.
    Retourne True si elles sont identiques.
    """

    if valeur1 is None or valeur2 is None:
        return False

    return valeur1 == valeur2


def comparer_montants(montant1, montant2, tolerance=None):
    """
    Compare deux montants financiers.
    """

    if montant1 is None or montant2 is None:
        return False

    montant1 = Decimal(str(montant1))
    montant2 = Decimal(str(montant2))

    limite = TOLERANCES_MONTANTS["defaut"] if tolerance is None else Decimal(str(tolerance))
    return abs(montant1 - montant2) <= limite


def _ecart_montant(montant1, montant2):
    """Écart absolu entre deux montants. 0 si une valeur est absente."""
    try:
        if montant1 is None or montant2 is None:
            return Decimal("0")
        return abs(Decimal(str(montant1)) - Decimal(str(montant2)))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def comparer_transaction(
    reference_partenaire,
    reference_amplitude,
    montant_partenaire,
    montant_amplitude,
    type_operation
):
    """
    Compare une transaction partenaire avec une transaction Amplitude.

    Retourne un dictionnaire contenant :
    - le résultat global
    - le détail de chaque comparaison
    """

    type_operation = type_operation.upper().strip()

    reference_identique = comparer_valeurs(
        reference_partenaire,
        reference_amplitude
    )

    montant_identique = comparer_montants(
        montant_partenaire,
        montant_amplitude
    )

    if type_operation not in [
        "ENVOI",
        "RETRAIT",
        "PAIEMENT",
        "REMBOURSEMENT"
    ]:
        raise ValueError(
            "Type d'opération invalide. "
            "Utilisez ENVOI, RETRAIT ou REMBOURSEMENT."
        )

    if reference_identique and montant_identique:
        resultat = "CORRESPONDANCE"

    elif reference_identique:
        resultat = "ANOMALIE"

    else:
        resultat = "NON_RAPPROCHEE"

    return {
        "resultat": resultat,
        "reference": reference_identique,
        "montant": montant_identique,
        "type_operation": type_operation
    }


def determiner_anomalie(resultat):
    """
    Détermine le type d'anomalie à partir
    du résultat de la comparaison.
    """

    if resultat["resultat"] == "CORRESPONDANCE":
        return None

    if not resultat.get("reference"):
        return {
            "type": "REFERENCE",
            "description": "Référence différente entre le partenaire et Amplitude."
        }

    if resultat.get("mttc") is False:
        return {
            "type": "MTTC",
            "description": "Différence de MTTC entre le partenaire et Amplitude."
        }

    if resultat.get("montant") is False:
        return {
            "type": "MONTANT",
            "description": "Différence de montant entre le partenaire et Amplitude."
        }

    if resultat.get("tva") is False:
        return {
            "type": "TVA",
            "description": "Différence de TVA entre le partenaire et Amplitude."
        }

    if resultat.get("tta") is False:
        return {
            "type": "TTA",
            "description": "Différence de TTA entre le partenaire et Amplitude."
        }

    if resultat.get("cte") is False:
        return {
            "type": "CTE",
            "description": "Différence de CTE entre le partenaire et Amplitude."
        }

    return {
        "type": "AUTRE",
        "description": "Écart détecté entre les deux transactions."
    }


def comparer_envoi(
    reference_partenaire,
    reference_amplitude,
    montant_partenaire,
    montant_amplitude,
    tva_partenaire,
    tva_amplitude,
    tta_partenaire,
    tta_amplitude,
    cte_partenaire,
    cte_amplitude,
    mttc_partenaire,
    mttc_amplitude
):
    """
    Compare une opération d'envoi entre un partenaire
    et Amplitude.
    """

    reference = comparer_valeurs(
        reference_partenaire,
        reference_amplitude
    )

    montant = comparer_montants(
        montant_partenaire,
        montant_amplitude
    )

    tva = comparer_montants(
        tva_partenaire,
        tva_amplitude
    )

    tta = comparer_montants(
        tta_partenaire,
        tta_amplitude
    )

    cte = comparer_montants(
        cte_partenaire,
        cte_amplitude
    )

    mttc = comparer_montants(
        mttc_partenaire,
        mttc_amplitude
    )

    if (
        reference
        and montant
        and tva
        and tta
        and cte
        and mttc
    ):
        resultat = "CORRESPONDANCE"

    elif reference:
        resultat = "ANOMALIE"

    else:
        resultat = "NON_RAPPROCHEE"

    return {
        "resultat": resultat,
        "reference": reference,
        "montant": montant,
        "tva": tva,
        "tta": tta,
        "cte": cte,
        "mttc": mttc,
        "score": calculer_score(
            {
                "reference": reference,
                "montant": montant,
                "tva": tva,
                "tta": tta,
                "cte": cte,
                "mttc": mttc,
            },
            "ENVOI",
        ),
    }


def rapprocher_envoi(
    reference_partenaire,
    reference_amplitude,
    montant_partenaire,
    montant_amplitude,
    tva_partenaire,
    tva_amplitude,
    tta_partenaire,
    tta_amplitude,
    cte_partenaire,
    cte_amplitude,
    mttc_partenaire,
    mttc_amplitude
):
    """
    Effectue le rapprochement d'un envoi
    entre un partenaire et Amplitude.
    """

    reference_ok = comparer_valeurs(
        reference_partenaire,
        reference_amplitude
    )

    montant_ok = comparer_montants(
        montant_partenaire,
        montant_amplitude
    )

    tva_ok = comparer_montants(
        tva_partenaire,
        tva_amplitude
    )

    tta_ok = comparer_montants(
        tta_partenaire,
        tta_amplitude
    )

    cte_ok = comparer_montants(
        cte_partenaire,
        cte_amplitude
    )

    mttc_ok = comparer_montants(
        mttc_partenaire,
        mttc_amplitude
    )

    ecart_mttc = _ecart_montant(mttc_partenaire, mttc_amplitude)

    if not reference_ok:
        resultat = "NON_RAPPROCHEE"

    elif ecart_mttc > 0:
        resultat = "ANOMALIE"

    elif (
        montant_ok
        and tva_ok
        and tta_ok
        and cte_ok
        and mttc_ok
    ):
        resultat = "CORRESPONDANCE"

    else:
        resultat = "ANOMALIE"

    return {
        "resultat": resultat,
        "reference": reference_ok,
        "montant": montant_ok,
        "tva": tva_ok,
        "tta": tta_ok,
        "cte": cte_ok,
        "mttc": mttc_ok,
        "ecart_mttc": ecart_mttc,
        "score": calculer_score(
            {
                "reference": reference_ok,
                "montant": montant_ok,
                "tva": tva_ok,
                "tta": tta_ok,
                "cte": cte_ok,
                "mttc": mttc_ok,
            },
            "ENVOI",
        ),
    }


def rapprocher_remboursement(
    reference_partenaire,
    reference_amplitude,
    mttc_partenaire,
    mttc_amplitude
):
    """
    Rapproche un remboursement.

    Critères :
    - référence
    - MTTC
    """

    reference_ok = comparer_valeurs(
        reference_partenaire,
        reference_amplitude
    )

    mttc_ok = comparer_montants(
        mttc_partenaire,
        mttc_amplitude
    )

    ecart_mttc = _ecart_montant(mttc_partenaire, mttc_amplitude)

    if not reference_ok:
        resultat = "NON_RAPPROCHEE"

    elif ecart_mttc > 0:
        resultat = "ANOMALIE"

    else:
        resultat = "CORRESPONDANCE"

    return {
        "resultat": resultat,
        "reference": reference_ok,
        "mttc": mttc_ok,
        "ecart_mttc": ecart_mttc,
        "score": calculer_score(
            {"reference": reference_ok, "mttc": mttc_ok},
            "REMBOURSEMENT",
        ),
    }


def rapprocher_retrait(**donnees):
    """Rapproche un retrait à partir du PIN et de la TTA à 2 % des frais."""
    reference_ok = comparer_valeurs(
        donnees.get("reference_partenaire"),
        donnees.get("reference_amplitude"),
    )
    frais_retrait = donnees.get("frais_retrait_partenaire")
    tta_attendue = None
    try:
        if frais_retrait is not None:
            tta_attendue = Decimal(str(frais_retrait)) * Decimal("0.02")
    except (InvalidOperation, ValueError, TypeError):
        pass

    tta_ok = comparer_montants(tta_attendue, donnees.get("tta_amplitude"))
    ecart_tta = _ecart_montant(tta_attendue, donnees.get("tta_amplitude"))

    if not reference_ok:
        resultat = "NON_RAPPROCHEE"
    elif tta_ok:
        resultat = "CORRESPONDANCE"
    else:
        resultat = "ANOMALIE"

    return {
        "resultat": resultat,
        "reference": reference_ok,
        "tta": tta_ok,
        "tta_attendue": tta_attendue,
        "ecart_tta": ecart_tta,
        "score": calculer_score(
            {"reference": reference_ok, "tta": tta_ok},
            "RETRAIT",
        ),
    }
def rapprocher_transaction(type_operation, **donnees):
    """
    Oriente une transaction vers la règle
    correspondant à son type d'opération.
    """

    if type_operation == "ENVOI":
        return rapprocher_envoi(**donnees)

    elif type_operation == "REMBOURSEMENT":
        return rapprocher_remboursement(**donnees)

    elif type_operation == "RETRAIT":
        return rapprocher_retrait(**donnees)

    else:
        return {
            "resultat": "ERREUR",
            "message": f"Type d'opération inconnu : {type_operation}"
        }


def _valeurs_pour_rapprochement(transaction):
    """
    Utilise les valeurs recalculées (RIA / YUBA) si elles existent,
    sinon les valeurs importées.
    """
    tva = transaction.tva_recalculee if getattr(transaction, "tva_recalculee", None) is not None else transaction.tva
    cte = transaction.cte_recalculee if getattr(transaction, "cte_recalculee", None) is not None else transaction.cte
    mttc = transaction.mttc_recalculee if getattr(transaction, "mttc_recalculee", None) is not None else transaction.mttc
    return tva, transaction.tta, cte, mttc


def _evaluer_paire(partenaire, amplitude, type_operation):
    if type_operation == "REMBOURSEMENT":
        _tvp, _tap, _ctp, mttc_p = _valeurs_pour_rapprochement(partenaire)
        _tva, _tta, _cta, mttc_a = _valeurs_pour_rapprochement(amplitude)
        return rapprocher_remboursement(partenaire.reference, amplitude.reference, mttc_p, mttc_a)
    if type_operation == "ENVOI":
        tva_p, tta_p, cte_p, mttc_p = _valeurs_pour_rapprochement(partenaire)
        tva_a, tta_a, cte_a, mttc_a = _valeurs_pour_rapprochement(amplitude)
        return rapprocher_envoi(
            partenaire.reference, amplitude.reference, partenaire.montant, amplitude.montant,
            tva_p, tva_a, tta_p, tta_a, cte_p, cte_a, mttc_p, mttc_a,
        )
    if type_operation == "RETRAIT":
        return rapprocher_retrait(
            reference_partenaire=partenaire.reference,
            reference_amplitude=amplitude.reference,
            frais_retrait_partenaire=partenaire.frais_envoi,
            tta_amplitude=amplitude.tta,
        )
    return {"resultat": "ERREUR", "message": f"Type operation inconnu : {type_operation}"}


def rapprocher_transactions_base(
    transactions_partenaire,
    transactions_amplitude,
    type_operation
):
    """
    Rapproche une liste de transactions partenaire
    avec une liste de transactions Amplitude.
    """

    correspondances = []
    anomalies = []
    non_rapprochees = []

    transactions_amplitude_restantes = list(
        transactions_amplitude
    )

    for partenaire in transactions_partenaire:

        evaluations = [
            (_evaluer_paire(partenaire, amplitude, type_operation), index, amplitude)
            for index, amplitude in enumerate(transactions_amplitude_restantes)
        ]
        evaluations = [item for item in evaluations if item[0].get("score") is not None]
        if not evaluations:
            non_rapprochees.append({
                "transaction": partenaire,
                "cote": "PARTENAIRE",
                "type": "ABSENCE",
                "description": "Aucune transaction candidate exploitable.",
                "details": {"score": Decimal("0")},
            })
            continue

        evaluations.sort(key=lambda item: item[0]["score"], reverse=True)
        resultat, index_trouve, transaction_trouvee = evaluations[0]
        score_max = resultat["score"]
        ex_aequo = sum(item[0]["score"] == score_max for item in evaluations) > 1
        resultat["candidate_ambigue"] = ex_aequo

        score = resultat.get("score")
        if score is not None:
            if score >= SEUILS_SCORE["automatique"] and not resultat.get("candidate_ambigue"):
                resultat["resultat"] = "CORRESPONDANCE"
            elif score >= SEUILS_SCORE["a_verifier"] or (resultat.get("candidate_ambigue") and score >= SEUILS_SCORE["anomalie"]):
                resultat["resultat"] = "A_VERIFIER"
            elif score >= SEUILS_SCORE["anomalie"]:
                resultat["resultat"] = "ANOMALIE"
            else:
                resultat["resultat"] = "NON_RAPPROCHEE"

        if resultat["resultat"] in ("CORRESPONDANCE", "A_VERIFIER"):

            resultat["automatique"] = resultat["resultat"] == "CORRESPONDANCE"
            correspondances.append({
                "partenaire": partenaire,
                "amplitude": transaction_trouvee,
                "details": resultat
            })

        elif resultat["resultat"] == "ANOMALIE":

            anomalies.append({
                "partenaire": partenaire,
                "amplitude": transaction_trouvee,
                "details": resultat
            })

        elif resultat["resultat"] == "EN_ATTENTE":

            non_rapprochees.append({
                "transaction": partenaire,
                "amplitude": transaction_trouvee,
                "cote": "PARTENAIRE",
                "type": "AUTRE",
                "description": resultat.get(
                    "message",
                    "Règle du retrait encore à confirmer."
                ),
                "details": resultat
            })

        else:

            non_rapprochees.append({
                "transaction": partenaire,
                "cote": "PARTENAIRE",
                "type": "NON_RAPPROCHEE",
                "details": resultat,
                "description": "Transaction non rapprochée."
            })

        if resultat.get("score", Decimal("0")) >= SEUILS_SCORE["anomalie"]:
            transactions_amplitude_restantes.remove(transaction_trouvee)

    for amplitude_restante in transactions_amplitude_restantes:
        non_rapprochees.append({
            "transaction": amplitude_restante,
            "cote": "AMPLITUDE",
            "type": "ABSENCE",
            "description": (
                "Aucune transaction partenaire "
                "avec cette référence."
            )
        })

    return {
        "correspondances": correspondances,
        "anomalies": anomalies,
        "non_rapprochees": non_rapprochees
    }
