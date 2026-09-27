from importations.regles_metier import (
    calculer_tva,
    calculer_cte,
    calculer_mttc,
    verifier_tva,
    verifier_cte,
    verifier_mttc
)


montant = 150000
frais_envoi = 10000
tta = 0

tva = calculer_tva(frais_envoi)
cte = calculer_cte(montant)

mttc = calculer_mttc(
    montant,
    tva,
    tta,
    cte
)

print("TVA :", tva)
print("CTE :", cte)
print("MTTC :", mttc)

print(
    "TVA correcte :",
    verifier_tva(frais_envoi, tva)
)

print(
    "CTE correcte :",
    verifier_cte(montant, cte)
)

print(
    "MTTC correct :",
    verifier_mttc(
        montant,
        tva,
        tta,
        cte,
        mttc
    )
)
from importations.regles_metier import verifier_conformite_envoi


resultat = verifier_conformite_envoi(
    montant=150000,
    customer_fee=10000,
    tva=1925,
    tta=0,
    cte=750,
    mttc=152675
)

print("\n=== CONTRÔLE DE CONFORMITÉ ===")
print("Conforme :", resultat["conforme"])
print("TVA conforme :", resultat["tva_conforme"])
print("CTE conforme :", resultat["cte_conforme"])
print("MTTC conforme :", resultat["mttc_conforme"])
print("\n=== TEST TVA INCORRECTE ===")

resultat_erreur = verifier_conformite_envoi(
    montant=150000,
    customer_fee=10000,
    tva=1500,       # TVA volontairement incorrecte
    tta=0,
    cte=750,
    mttc=152250
)

print("Conforme :", resultat_erreur["conforme"])
print("TVA conforme :", resultat_erreur["tva_conforme"])
print("TVA attendue :", resultat_erreur["tva_attendue"])
print("TVA fournie :", 1500)

from importations.regles_metier import obtenir_anomalies_conformite


print("\n=== ANOMALIES DE CONFORMITÉ ===")

anomalies = obtenir_anomalies_conformite(
    resultat_erreur
)

for anomalie in anomalies:
    print(
        anomalie["type"],
        ":",
        anomalie["description"]
    )
from importations.regles_metier import recalculer_envoi_ria_yuba


print("\n=== RECALCUL RIA / YUBA ===")

resultat = recalculer_envoi_ria_yuba(
    montant=150000,
    customer_fee=10000,
    tta=0
)

print("Montant :", resultat["montant"])
print("Customer Fee :", resultat["customer_fee"])
print("TVA recalculée :", resultat["tva"])
print("TTA :", resultat["tta"])
print("CTE recalculée :", resultat["cte"])
print("MTTC recalculé :", resultat["mttc"])

