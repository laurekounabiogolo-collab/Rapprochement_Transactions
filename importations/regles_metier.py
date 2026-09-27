from decimal import Decimal


TAUX_TVA_RIA_YUBA = Decimal("0.1925")
TAUX_CTE_RIA_YUBA = Decimal("0.005")


def calculer_tva(frais_envoi):
    """
    Calcule la TVA à partir des frais d'envoi.
    """
    if frais_envoi is None:
        return Decimal("0.00")

    return Decimal(str(frais_envoi)) * TAUX_TVA_RIA_YUBA


def calculer_cte(montant):
    """
    Calcule la CTE à partir du montant envoyé.
    """
    if montant is None:
        return Decimal("0.00")

    return Decimal(str(montant)) * TAUX_CTE_RIA_YUBA


def calculer_mttc(montant, tva, tta, cte):
    """
    Calcule le MTTC.
    """
    montant = Decimal(str(montant or 0))
    tva = Decimal(str(tva or 0))
    tta = Decimal(str(tta or 0))
    cte = Decimal(str(cte or 0))

    return montant + tva + tta + cte
def verifier_tva(frais_envoi, tva):
    """
    Vérifie que la TVA correspond à 19,25 % des frais d'envoi.
    """

    tva_attendue = calculer_tva(frais_envoi)

    tva_recue = Decimal(str(tva or 0))

    return tva_recue == tva_attendue


def verifier_cte(montant, cte):
    """
    Vérifie que la CTE correspond à 0,5 % du montant.
    """

    cte_attendue = calculer_cte(montant)

    cte_recue = Decimal(str(cte or 0))

    return cte_recue == cte_attendue


def verifier_mttc(montant, tva, tta, cte, mttc):
    """
    Vérifie que le MTTC correspond à :
    montant + TVA + TTA + CTE.
    """

    mttc_attendu = calculer_mttc(
        montant,
        tva,
        tta,
        cte
    )

    mttc_recu = Decimal(str(mttc or 0))

    return mttc_recu == mttc_attendu    
def verifier_conformite_envoi(
    montant,
    customer_fee,
    tva,
    tta,
    cte,
    mttc
):
    """
    Vérifie la conformité d'un envoi RIA ou YUBA.

    Règles :
    TVA = 19,25 % du Customer Fee
    CTE = 0,5 % du montant
    MTTC = montant + TVA + TTA + CTE
    """

    montant = Decimal(str(montant or 0))
    customer_fee = Decimal(str(customer_fee or 0))
    tva = Decimal(str(tva or 0))
    tta = Decimal(str(tta or 0))
    cte = Decimal(str(cte or 0))
    mttc = Decimal(str(mttc or 0))

    tva_attendue = customer_fee * TAUX_TVA_RIA_YUBA
    cte_attendue = montant * TAUX_CTE_RIA_YUBA
    mttc_attendu = montant + tva + tta + cte

    tva_conforme = tva == tva_attendue
    cte_conforme = cte == cte_attendue
    mttc_conforme = mttc == mttc_attendu

    conforme = (
        tva_conforme
        and cte_conforme
        and mttc_conforme
    )

    return {
        "conforme": conforme,
        "tva_conforme": tva_conforme,
        "cte_conforme": cte_conforme,
        "mttc_conforme": mttc_conforme,
        "tva_attendue": tva_attendue,
        "cte_attendue": cte_attendue,
        "mttc_attendu": mttc_attendu,
    }
def obtenir_anomalies_conformite(resultat):
    """
    Retourne la liste des anomalies détectées
    lors du contrôle de conformité.
    """

    anomalies = []

    if not resultat["tva_conforme"]:
        anomalies.append({
            "type": "TVA",
            "description": (
                f"TVA non conforme. "
                f"Attendue : {resultat['tva_attendue']}, "
                f"fournie par le partenaire : différence détectée."
            )
        })

    if not resultat["cte_conforme"]:
        anomalies.append({
            "type": "CTE",
            "description": (
                f"CTE non conforme. "
                f"Attendue : {resultat['cte_attendue']}."
            )
        })

    if not resultat["mttc_conforme"]:
        anomalies.append({
            "type": "MTTC",
            "description": (
                f"MTTC non conforme. "
                f"Attendu : {resultat['mttc_attendu']}."
            )
        })

    return anomalies


def recalculer_envoi_ria_yuba(
    montant,
    customer_fee,
    tta
):
    """
    Recalcule les valeurs réglementaires d'un envoi
    RIA ou YUBA avant le rapprochement.

    TVA = 19,25 % du Customer Fee
    CTE = 0,5 % du montant
    MTTC = montant + TVA + TTA + CTE
    """

    montant = Decimal(str(montant or 0))
    customer_fee = Decimal(str(customer_fee or 0))
    tta = Decimal(str(tta or 0))

    tva = customer_fee * Decimal("0.1925")

    cte = montant * Decimal("0.005")

    mttc = montant + tva + tta + cte

    return {
        "montant": montant,
        "customer_fee": customer_fee,
        "tva": tva,
        "tta": tta,
        "cte": cte,
        "mttc": mttc
    }
    
