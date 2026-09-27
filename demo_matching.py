from rapprochement.matching import comparer_envoi
from rapprochement.matching import rapprocher_transaction


resultat = comparer_envoi(
    "RIA001",
    "RIA001",

    150000,
    150000,

    1925,
    1925,

    0,
    0,

    750,
    750,

    152675,
    152675
)


print("Résultat :", resultat["resultat"])

print("Référence :", "OK" if resultat["reference"] else "DIFFÉRENTE")
print("Montant   :", "OK" if resultat["montant"] else "DIFFÉRENT")
print("TVA       :", "OK" if resultat["tva"] else "DIFFÉRENTE")
print("TTA       :", "OK" if resultat["tta"] else "DIFFÉRENTE")
print("CTE       :", "OK" if resultat["cte"] else "DIFFÉRENTE")
print("MTTC      :", "OK" if resultat["mttc"] else "DIFFÉRENT")

from rapprochement.matching import rapprocher_envoi


resultat = rapprocher_envoi(
    "RIA001",
    "RIA001",
    150000,
    150000,
    1925,
    1925,
    0,
    0,
    750,
    750,
    152675,
    152675
)

print("\n=== RAPPROCHEMENT ENVOI ===")
print("Résultat :", resultat["resultat"])
print("Référence :", resultat["reference"])
print("Montant :", resultat["montant"])
print("TVA :", resultat["tva"])
print("TTA :", resultat["tta"])
print("CTE :", resultat["cte"])
print("MTTC :", resultat["mttc"])
print("Écart MTTC :", resultat["ecart_mttc"])

resultat_ecart = rapprocher_envoi(
    "RIA002",
    "RIA002",

    150000,
    150000,

    1925,
    1925,

    0,
    0,

    750,
    750,

    152675,
    152000
)

print("\n=== TEST ÉCART MTTC ===")
print("Résultat :", resultat_ecart["resultat"])
print("Référence :", resultat_ecart["reference"])
print("MTTC partenaire :", 152675)
print("MTTC Amplitude :", 152000)
print("Écart MTTC :", resultat_ecart["ecart_mttc"])

resultat_reference = rapprocher_envoi(
    "RIA003",
    "RIA999",

    150000,
    150000,

    1925,
    1925,

    0,
    0,

    750,
    750,

    152675,
    152675
)

print("\n=== TEST RÉFÉRENCE DIFFÉRENTE ===")
print("Résultat :", resultat_reference["resultat"])
print("Référence :", resultat_reference["reference"])
print("Montant :", resultat_reference["montant"])
print("MTTC :", resultat_reference["mttc"])
print("Écart MTTC :", resultat_reference["ecart_mttc"])


from rapprochement.matching import rapprocher_remboursement


resultat = rapprocher_remboursement(
    "MG100",
    "MG100",
    152675,
    152675
)

print("\n=== TEST REMBOURSEMENT ===")
print("Résultat :", resultat["resultat"])
print("Référence :", resultat["reference"])
print("MTTC :", resultat["mttc"])
print("Écart MTTC :", resultat["ecart_mttc"])


resultat = rapprocher_transaction(
    "REMBOURSEMENT",
    reference_partenaire="MG100",
    reference_amplitude="MG100",
    mttc_partenaire=152675,
    mttc_amplitude=152675
)

print("\n=== MOTEUR PRINCIPAL ===")
print("Résultat :", resultat["resultat"])