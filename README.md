# Rapprochement ERA — BANGE Bank Cameroun

Application Django de gestion des imports et de rapprochement de transactions entre des partenaires de transfert et la source bancaire Amplitude.

Ce guide décrit l’installation et l’utilisation en environnement local. Il ne constitue pas un guide de déploiement en production : aucun serveur cible ni processus de déploiement n’est défini dans le dépôt.

## Fonctionnalités

- Gestion des utilisateurs avec les rôles Agent ERA, Responsable ERA et Directeur OMT.
- Gestion des sources de données (partenaires et banques).
- Import des fichiers CSV et Excel (XLS/XLSX).
- Normalisation des champs et détection des imports et transactions en doublon.
- Rapprochement des envois, retraits et remboursements.
- Consultation des correspondances, anomalies et transactions non rapprochées.
- Rapports statistiques avec export CSV et PDF.

L’extraction du texte PDF existe dans le code, mais les fichiers PDF ne sont pas acceptés par le formulaire d’import et ne sont pas transformés en lignes de transactions. Utilisez un export CSV ou Excel.

## Prérequis

- Python dans une version compatible avec Django 6.1.
- PostgreSQL accessible depuis l’application.
- Les dépendances de `requirements.txt`.

## Installation locale (Windows PowerShell)

Depuis la racine du projet :

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Si l’environnement virtuel `venv` existe déjà, activez-le et installez les dépendances avec `pip install -r requirements.txt`.

## Configuration de l'environnement

Django lit sa clé, le mode debug, les hôtes autorisés et les paramètres PostgreSQL depuis les variables d'environnement. Aucune clé secrète ni aucun mot de passe de base de données ne doit être enregistré dans le dépôt.

Pour un terminal PowerShell local, définissez ces variables après avoir activé l'environnement virtuel et avant les commandes Django :

~~~powershell
$env:DJANGO_SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(50))"
$env:DJANGO_DEBUG = "true"
$env:DJANGO_ALLOWED_HOSTS = "localhost,127.0.0.1"

$env:POSTGRES_DB = "rapprochement_db"
$env:POSTGRES_USER = "postgres"
$env:POSTGRES_HOST = "localhost"
$env:POSTGRES_PORT = "5432"
$secureDbPassword = Read-Host "Mot de passe PostgreSQL" -AsSecureString
$env:POSTGRES_PASSWORD = [System.Net.NetworkCredential]::new("", $secureDbPassword).Password
~~~

Adaptez les valeurs PostgreSQL à votre installation. Ces variables ne sont définies que pour le terminal courant. Configurez-les dans le gestionnaire de secrets ou l'environnement du service pour un usage persistant.

Pour une mise en production, définissez une clé secrète propre à l'application, DJANGO_DEBUG=false, et DJANGO_ALLOWED_HOSTS avec les noms d'hôtes réels, séparés par des virgules. Les cinq variables POSTGRES_* doivent aussi pointer vers la base de production. Le démarrage échoue explicitement si la clé, les paramètres PostgreSQL ou, en mode production, la liste des hôtes autorisés manquent.

## Initialisation

Appliquez les migrations :

```powershell
python manage.py migrate
```

Créez un compte administrateur :

```powershell
python manage.py createsuperuser
```

Démarrez le serveur local :

```powershell
python manage.py runserver
```

Ouvrez ensuite <http://127.0.0.1:8000/>.

Après connexion, créez les sources nécessaires depuis **Sources de données** ou l’administration Django. Pour le parcours de rapprochement standard, il faut au moins :

- une source partenaire de type **Partenaire de transfert** (par exemple RIA ou YUBA) ;
- une source nommée **Amplitude**, de type **Système bancaire** et active.

Le nom Amplitude est utilisé par le code pour distinguer les fichiers bancaires.

## Parcours utilisateur

1. Connectez-vous avec un compte autorisé.
2. Ouvrez **Importations**.
3. Importez le fichier du partenaire : choisissez la source, le type d’opération et le fichier.
4. Importez le fichier Amplitude correspondant avec le même type d’opération.
5. Lorsque les deux imports contiennent des transactions, le bouton **Lancer un rapprochement** devient disponible sur la page d’importation.
6. Choisissez le partenaire, le type d’opération et les deux fichiers, puis lancez le rapprochement.
7. Consultez les résultats dans **Rapprochements**, **Correspondances**, **Anomalies** et **Non rapprochées**.

Le serveur vérifie également la présence de transactions dans les deux fichiers avant de créer un rapprochement. Un fichier traité mais sans transaction importée ne suffit pas.

Les fichiers chargés sont conservés sous `media/imports/`. Les fichiers d’erreurs d’import peuvent être téléchargés au format CSV depuis l’historique.

## Formats d’import

Les formats acceptés par le formulaire sont CSV, XLS et XLSX. Pour les CSV, le lecteur essaie le point-virgule, puis la virgule si le fichier n’a été lu qu’en une seule colonne.

Champs internes principaux :

- obligatoires pour enregistrer une transaction : référence, montant et date ;
- facultatifs : devise, TVA, TTA, CTE, MTTC, frais d’envoi, nom de l’émetteur et nom du bénéficiaire.

Le service d’import reconnaît plusieurs alias courants, notamment `reference`, `ref`, `send_order_number`, `pin`, `amount`, `principal`, `date_transaction`, `dco`, `customer_fee`, `tva`, `tta`, `cte`, `mttc` et `dev`. Les noms de colonnes sont nettoyés (minuscules, espaces et tirets remplacés).

Des fichiers d’exemple se trouvent dans `exemples/` :

- `ria_envois.csv`
- `amplitude_envois.csv`

## Règles de rapprochement

Le moteur applique des règles fixes ; il ne s’agit pas d’un modèle d’apprentissage automatique. Il cherche une référence strictement identique, puis compare les montants prévus pour le type d’opération. La date n’est pas un critère du matching actuel.

| Opération | Comparaisons | Poids du score |
|---|---|---|
| Envoi | Référence, montant, TVA, TTA, CTE et MTTC | 40, 20, 10, 10, 10 et 10 |
| Remboursement | Référence et MTTC | 50 et 50 |
| Retrait | Référence/PIN et TTA | 50 et 50 |

Pour les envois RIA/YUBA, le service recalcule les valeurs réglementaires avant le rapprochement : TVA = 19,25 % des frais d’envoi ; CTE = 0,5 % du montant ; MTTC = montant + TVA + TTA + CTE. Pour un retrait, la TTA attendue est calculée à 2 % des frais du partenaire.

Une référence identique avec un écart financier produit une anomalie. Une référence sans correspondance produit une transaction non rapprochée.

## Rôles et permissions

- **Agent ERA** : importe, lance et consulte les rapprochements ; ne gère pas les sources ni les comptes.
- **Responsable ERA** : peut aussi gérer les sources et comptes d’agents, traiter les anomalies, valider les résultats et générer les PDF.
- **Directeur OMT** : peut gérer les sources et les comptes, valider les résultats et générer les PDF.
- **Superutilisateur Django** : accès privilégié dans les contrôles applicatifs.

Les permissions sont vérifiées côté serveur, pas seulement en masquant les liens de navigation.

## Rapports

La page **Rapports** propose des filtres par dates et partenaire, des statistiques, un export CSV et un export PDF. La génération PDF est réservée au Responsable ERA et au Directeur OMT.

## Tests

Pour exécuter les tests Django :

```powershell
python manage.py test
```

Une base PostgreSQL de test accessible peut être nécessaire selon la configuration Django.

## Structure du projet

- `config/` : paramètres et routes Django.
- `utilisateurs/` : comptes, authentification, rôles et permissions.
- `SourceDonnees/` : sources de données, formulaire et vues de gestion.
- `importations/` : lecture, normalisation et enregistrement des fichiers.
- `transactions/` : modèle, consultation et modification des transactions.
- `rapprochement/` : moteur, résultats et traitement des anomalies.
- `rapports/` : statistiques et exports.
- `templates/` et `static/` : interface, styles et JavaScript.
- `media/imports/` : fichiers importés localement.
- `exemples/` : jeux de données d’exemple.

## Limites et points à régler avant une mise en production

- Le déploiement (serveur, processus web, HTTPS, fichiers statiques et médias, sauvegardes) dépend de l’environnement cible et n’est pas configuré dans le dépôt.
- La clé secrète et les identifiants de base ne doivent pas rester dans le code ; externalisez-les avant le déploiement.
- `DEBUG` doit être désactivé et `ALLOWED_HOSTS` configuré pour l’environnement réel.
- Prévoir une politique de sauvegarde PostgreSQL et de rétention de `media/imports/`.
