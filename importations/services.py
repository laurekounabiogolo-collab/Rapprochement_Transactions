import hashlib
from decimal import Decimal, InvalidOperation

import pandas as pd
from django.utils import timezone as dj_timezone
from pypdf import PdfReader

from SourceDonnees.models import SourceDonnees
from importations.regles_metier import recalculer_envoi_ria_yuba
from transactions.models import Transaction


def lire_fichier_csv(chemin_fichier):
    """
    Lit un fichier CSV et retourne les données sous forme de DataFrame.
    """

    try:
        donnees = pd.read_csv(
            chemin_fichier,
            sep=";",
        )
        if donnees.shape[1] == 1:
            donnees = pd.read_csv(chemin_fichier, sep=",")
        donnees = nettoyer_colonnes(donnees)
        return donnees

    except Exception as erreur:
        print(f"Erreur lors de la lecture du fichier : {erreur}")
        return None


def lire_fichier_excel(chemin_fichier):
    """
    Lit un fichier Excel et retourne les données
    sous forme de DataFrame.
    """

    try:
        donnees = pd.read_excel(chemin_fichier)
        donnees = nettoyer_colonnes(donnees)
        return donnees

    except Exception as erreur:
        print(f"Erreur lors de la lecture du fichier Excel : {erreur}")
        return None


def lire_fichier_pdf(chemin_fichier):
    """
    Extrait le texte d'un fichier PDF.

    Cette première version sert à vérifier que le PDF
    est lisible. La transformation en tableau sera
    traitée ensuite.
    """

    try:
        lecteur = PdfReader(chemin_fichier)
        texte = ""
        for page in lecteur.pages:
            contenu = page.extract_text()
            if contenu:
                texte += contenu + "\n"
        return texte

    except Exception as erreur:
        print(f"Erreur lors de la lecture du PDF : {erreur}")
        return None


def normaliser_texte(texte):
    """
    Nettoie et uniformise un texte.
    """
    if pd.isna(texte):
        return ""

    texte = str(texte)
    texte = texte.strip()
    texte = " ".join(texte.split())
    texte = texte.lower()

    return texte


def normaliser_date(date):
    """
    Convertit une date en objet datetime.
    """
    try:
        valeur = pd.to_datetime(date, dayfirst=True)
        if pd.isna(valeur):
            return None
        dt = valeur.to_pydatetime()
        if dj_timezone.is_naive(dt):
            return dj_timezone.make_aware(dt, dj_timezone.get_current_timezone())
        return dt
    except Exception:
        return None


def normaliser_reference(reference):
    """
    Nettoie et uniformise une référence de transaction.
    """
    if pd.isna(reference):
        return ""

    reference = str(reference)
    reference = reference.strip()
    reference = reference.upper()

    return reference


def normaliser_montant(montant):
    """
    Convertit un montant en nombre.
    """
    try:
        if pd.isna(montant) or montant is None or str(montant).strip() == "":
            return None
        montant = str(montant)
        montant = montant.replace(" ", "")
        montant = montant.replace(",", ".")
        return float(montant)
    except Exception:
        return None


def nettoyer_colonnes(donnees):
    """
    Nettoie les noms des colonnes d'un fichier importé.
    """

    donnees.columns = (
        donnees.columns
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )

    return donnees


def renommer_colonnes(donnees, correspondances):
    """
    Renomme les colonnes d'un fichier selon un dictionnaire
    de correspondance.
    """

    donnees = donnees.rename(columns=correspondances)
    return donnees


COLONNES_RIA = {
    "product": "produit",
    "send_order_number": "reference",
    "pin": "reference",
    "customer_fee": "frais_envoi",
    "amount": "montant",
    "tva": "tva",
    "tta": "tta",
    "cte": "cte",
    "mttc": "mttc",
}

COLONNES_AMPLITUDE = {
    "reference": "reference",
    "montant": "montant",
    "tva": "tva",
    "tta": "tta",
    "cte": "cte",
    "mttc": "mttc",
    "dco": "date",
    "dev": "devise",
}

ALIAS_COLONNES = {
    "reference": [
        "reference", "ref", "ref_operation", "send_order_number",
        "pin", "mtcn", "no_reference", "numero_reference",
        "transaction_id", "id_transaction", "ref_externe",
    ],
    "montant": [
        "montant", "amount", "principal", "montant_envoye",
        "montant_principal", "send_amount", "principal_amount",
    ],
    "date": [
        "date", "date_transaction", "dco", "transaction_date",
        "date_operation", "date_envoi", "date_retrait",
    ],
    "nom_emetteur": [
        "nom_emetteur", "sender", "expediteur", "sender_name",
        "nom_expediteur", "client",
    ],
    "nom_beneficiaire": [
        "nom_beneficiaire", "beneficiary", "beneficiaire",
        "receiver", "receiver_name", "destinataire",
    ],
    "tva": ["tva"],
    "tta": ["tta"],
    "cte": ["cte"],
    "mttc": ["mttc", "montant_ttc"],
    "frais_envoi": [
        "frais_envoi", "customer_fee", "fee", "frais", "commission",
        "frais_retrait", "withdrawal_fee", "withdrawal_fees", "retrait_fee",
    ],
    "devise": ["devise", "dev", "currency", "ccy"],
}


def appliquer_alias_colonnes(donnees):
    """Mappe les colonnes connues vers le schéma interne sans écraser."""
    renommage = {}
    colonnes = list(donnees.columns)
    for cible, alias in ALIAS_COLONNES.items():
        if cible in colonnes:
            continue
        for nom in alias:
            if nom in colonnes and nom != cible:
                renommage[nom] = cible
                break
    if renommage:
        donnees = donnees.rename(columns=renommage)
    return donnees


def normaliser_colonnes_source(donnees, source):
    """
    Adapte les noms des colonnes selon la source du fichier.
    """

    source = source.lower().strip()

    if source == "ria":
        donnees = renommer_colonnes(donnees, COLONNES_RIA)
    elif source == "amplitude":
        donnees = renommer_colonnes(donnees, COLONNES_AMPLITUDE)

    return appliquer_alias_colonnes(donnees)


def lire_fichier(chemin_fichier):
    """
    Détecte automatiquement le format du fichier
    et utilise le lecteur approprié.
    """

    chemin = str(chemin_fichier).lower()

    if chemin.endswith(".csv"):
        return lire_fichier_csv(chemin_fichier)

    elif chemin.endswith(".xlsx") or chemin.endswith(".xls"):
        return lire_fichier_excel(chemin_fichier)

    elif chemin.endswith(".pdf"):
        return lire_fichier_pdf(chemin_fichier)

    else:
        raise ValueError(
            "Format de fichier non pris en charge. "
            "Formats acceptés : CSV, XLSX, XLS, PDF."
        )


def preparer_transactions(donnees):
    """
    Prépare les données importées avant leur enregistrement
    dans la base de données.
    """

    if "date" not in donnees.columns and "date_transaction" in donnees.columns:
        donnees["date"] = donnees["date_transaction"]

    for col in ["reference", "montant", "date", "nom_emetteur", "nom_beneficiaire"]:
        if col not in donnees.columns:
            donnees[col] = None

    donnees["reference"] = donnees["reference"].apply(normaliser_reference)
    donnees["montant"] = donnees["montant"].apply(normaliser_montant)
    donnees["date"] = donnees["date"].apply(normaliser_date)
    donnees["nom_emetteur"] = donnees["nom_emetteur"].apply(normaliser_texte)
    donnees["nom_beneficiaire"] = donnees["nom_beneficiaire"].apply(normaliser_texte)

    for champ in ["tva", "tta", "cte", "mttc", "frais_envoi"]:
        if champ in donnees.columns:
            donnees[champ] = donnees[champ].apply(normaliser_montant)

    return donnees


def _decimal_ou_none(valeur):
    if valeur is None or (isinstance(valeur, float) and pd.isna(valeur)):
        return None
    try:
        return Decimal(str(valeur))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _est_ria_ou_yuba(nom_source):
    nom = (nom_source or "").upper()
    return "RIA" in nom or "YUBA" in nom


def transaction_deja_presente(source, reference, date_transaction, montant):
    """Protection contre les doublons : ne supprime jamais les existants."""
    filtres = {
        "source": source,
        "reference": reference,
        "montant": montant,
    }
    qs = Transaction.objects.filter(**filtres)
    if date_transaction:
        qs = qs.filter(date_transaction=date_transaction)
    return qs.exists()


def enregistrer_transactions(
    donnees,
    nom_source,
    fichier_importe=None,
    type_operation=None,
):
    """
    Enregistre les transactions préparées dans PostgreSQL.
    Ne supprime aucune donnée existante.
    """

    source = SourceDonnees.objects.get(nom=nom_source)
    transactions_creees = []
    ignorees = 0
    erreurs = []

    appliquer_regle = (
        _est_ria_ou_yuba(nom_source)
        and type_operation == Transaction.TypeOperation.ENVOI
    )

    for index, ligne in donnees.iterrows():
        reference = ligne.get("reference") or ""
        if not reference:
            erreurs.append(f"Ligne {index}: référence manquante.")
            continue

        montant = _decimal_ou_none(ligne.get("montant"))
        if montant is None:
            erreurs.append(f"Ligne {index} ({reference}): montant invalide.")
            continue

        date_tx = ligne.get("date")
        if date_tx is None:
            erreurs.append(f"Ligne {index} ({reference}): date invalide.")
            continue

        if transaction_deja_presente(source, reference, date_tx, montant):
            ignorees += 1
            continue

        tva = _decimal_ou_none(ligne.get("tva")) if "tva" in donnees.columns else None
        tta = _decimal_ou_none(ligne.get("tta")) if "tta" in donnees.columns else None
        cte = _decimal_ou_none(ligne.get("cte")) if "cte" in donnees.columns else None
        mttc = _decimal_ou_none(ligne.get("mttc")) if "mttc" in donnees.columns else None
        frais = _decimal_ou_none(ligne.get("frais_envoi")) if "frais_envoi" in donnees.columns else None

        tva_recalculee = None
        cte_recalculee = None
        mttc_recalculee = None

        if appliquer_regle:
            calcule = recalculer_envoi_ria_yuba(montant, frais, tta)
            tva_recalculee = calcule["tva"]
            cte_recalculee = calcule["cte"]
            mttc_recalculee = calcule["mttc"]

        devise = "XAF"
        if "devise" in donnees.columns and not pd.isna(ligne.get("devise")):
            devise = str(ligne.get("devise")).strip().upper() or "XAF"

        transaction = Transaction.objects.create(
            reference=reference,
            source=source,
            fichier_importe=fichier_importe,
            type_operation=type_operation,
            date_transaction=date_tx,
            montant=montant,
            devise=devise,
            tva=tva,
            tta=tta,
            cte=cte,
            mttc=mttc,
            tva_recalculee=tva_recalculee,
            cte_recalculee=cte_recalculee,
            mttc_recalculee=mttc_recalculee,
            frais_envoi=frais,
            nom_emetteur=ligne.get("nom_emetteur") or "",
            nom_beneficiaire=ligne.get("nom_beneficiaire") or "",
        )
        transactions_creees.append(transaction)

    return {
        "creees": transactions_creees,
        "ignorees": ignorees,
        "erreurs": erreurs,
    }


def calculer_empreinte(contenu):
    return hashlib.sha256(contenu).hexdigest()


def importer_depuis_chemin(
    chemin_fichier,
    nom_source,
    fichier_importe=None,
    type_operation=None,
):
    """
    Enchaîne lecture, mapping, normalisation et enregistrement.
    """
    donnees = lire_fichier(chemin_fichier)
    if donnees is None:
        return {
            "ok": False,
            "message": "Impossible de lire le fichier (format CSV/Excel attendu).",
        }
    if isinstance(donnees, str):
        return {
            "ok": False,
            "message": (
                "Le PDF a été lu mais n'est pas encore converti en tableau. "
                "Utilisez un export CSV."
            ),
        }

    donnees = normaliser_colonnes_source(donnees, nom_source)
    donnees = preparer_transactions(donnees)
    resultat = enregistrer_transactions(
        donnees,
        nom_source,
        fichier_importe=fichier_importe,
        type_operation=type_operation,
    )
    return {
        "ok": True,
        "creees": resultat["creees"],
        "ignorees": resultat["ignorees"],
        "erreurs": resultat["erreurs"],
    }
