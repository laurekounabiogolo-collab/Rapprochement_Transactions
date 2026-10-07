from functools import lru_cache

from django.core.exceptions import ImproperlyConfigured


SEUIL_REJET_MINIMUM = 0.04
SEUIL_SIMILARITE_MINIMUM = 0.12


@lru_cache(maxsize=8)
def _entrainer(snapshot):
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import FeatureUnion, make_pipeline
    except ImportError as erreur:
        raise ImproperlyConfigured(
            "scikit-learn n'est pas installé. Installe les dépendances du projet."
        ) from erreur

    phrases = []
    etiquettes = []
    for code, exemples in snapshot:
        for exemple in exemples:
            phrases.append(exemple)
            etiquettes.append(code)

    if len(set(etiquettes)) < 2:
        raise ValueError("Ajoute au moins deux intentions actives avec des exemples.")

    caracteristiques = FeatureUnion([
        ("mots", TfidfVectorizer(
            lowercase=True,
            strip_accents="unicode",
            ngram_range=(1, 2),
            sublinear_tf=True,
        )),
        ("caracteres", TfidfVectorizer(
            analyzer="char_wb",
            lowercase=True,
            strip_accents="unicode",
            ngram_range=(3, 5),
            sublinear_tf=True,
        )),
    ])
    modele = make_pipeline(
        caracteristiques,
        LogisticRegression(max_iter=2000, class_weight="balanced"),
    )
    modele.fit(phrases, etiquettes)
    matrice_exemples = modele.named_steps["featureunion"].transform(phrases)
    return modele, matrice_exemples


def predire_reponse(question, intentions):
    donnees = []
    reponses = {}
    for intention in intentions:
        exemples = intention.obtenir_exemples()
        if exemples:
            donnees.append((intention.code, tuple(exemples)))
            reponses[intention.code] = intention.reponse

    snapshot = tuple(donnees)
    if len(snapshot) < 2:
        return None, "Le chatbot a besoin d’au moins deux intentions actives avec des exemples."

    modele, matrice_exemples = _entrainer(snapshot)
    probabilites = modele.predict_proba([question])[0]
    meilleur_index = probabilites.argmax()
    code = modele.classes_[meilleur_index]
    seuil_score = max(SEUIL_REJET_MINIMUM, 1.5 / len(modele.classes_))

    vecteur_question = modele.named_steps["featureunion"].transform([question])
    similarite_max = float((vecteur_question @ matrice_exemples.T).max())

    if float(probabilites[meilleur_index]) < seuil_score or similarite_max < SEUIL_SIMILARITE_MINIMUM:
        return None, "Je ne reconnais pas encore cette question. Essaie de la reformuler."

    return code, reponses[code]
