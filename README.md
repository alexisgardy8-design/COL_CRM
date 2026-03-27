# CRM 

CRM de prospection partenaires, construit avec **Streamlit** et **Supabase**.
Permet de gérer les entreprises cibles, leurs contacts, le pipeline d'opportunités et l'historique des échanges.

---

## Prérequis

| Outil | Version minimale |
|---|---|
| Python | 3.12 |
| Compte Supabase | gratuit suffisant |
| n8n (optionnel) | pour les notifications webhook |

---

## Installation

```bash
# 1. Cloner le dépôt
git clone <url-du-repo> && cd CRM

# 2. Créer et activer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

# 3. Installer les dépendances
pip install -r requirements.txt
```

### Variables d'environnement

Créer un fichier `.env` à la racine :

```env
SUPABASE_URL=https://<votre-projet>.supabase.co
SUPABASE_KEY=<votre-anon-key>

# Optionnel — URL du webhook n8n (deals gagnés)
N8N_WEBHOOK_URL=http://localhost:5678/webhook/deal-gagne
```

### Lancer l'application

```bash
streamlit run app.py
```

L'app s'ouvre sur `http://localhost:8501`.

---

## Structure du projet

```
CRM/
├── app.py                  # Page d'accueil — Dashboard + relances du jour
├── db.py                   # Couche d'accès Supabase (toutes les requêtes)
├── utils.py                # CSS injecté et helpers partagés
├── pages/
│   ├── entreprises.py      # Gestion entreprises, contacts et opportunités
│   ├── opportunites.py     # Pipeline complet (Kanban + tableau)
│   └── interactions.py     # Journal des échanges par opportunité
├── requirements.txt
└── .env                    # Non versionné — à créer manuellement
```

---

## Pages et fonctionnalités

### Dashboard (`app.py`)

Page d'accueil avec :
- **5 KPIs** : prospects actifs, pipeline total, pipeline pondéré, deals gagnés, montant gagné
- **Relances du jour** : liste des opportunités dont la date de relance est aujourd'hui
- **Tableau récapitulatif** du pipeline par statut
- **10 dernières opportunités** ajoutées

### Entreprises (`pages/entreprises.py`)

- Ajouter / modifier / supprimer une entreprise
  - Champs : nom, secteur, ville, code postal, taille (TPE / PME / ETI / GE / ASSOCIATION / FONDATION), téléphone, site web, notes
- **Ajouter un contact** à une entreprise
  - Champs : prénom, nom, poste, email, téléphone, LinkedIn URL, contact principal
- **Modifier un contact existant** via l'expander "Voir / modifier les contacts"
- **Ajouter une opportunité** depuis la fiche entreprise
  - Bloqué si aucun contact n'existe pour cette entreprise
  - Sélection du contact obligatoire avant enregistrement

> La suppression d'une entreprise supprime en cascade ses contacts, opportunités et interactions (géré côté Supabase).

### Opportunités (`pages/opportunites.py`)

- Vue **Cards** (Kanban par statut) ou vue **Tableau**
- Filtres : statut, recherche texte, tri
- KPIs filtrés : nombre d'opportunités, pipeline total, pipeline pondéré
- **Changer le statut** directement depuis une card
- **Modifier une opportunité** (bouton "Modifier" sur chaque card) :
  - Champs : titre, montant visé, statut, probabilité, date de relance, date de closing (si gagné/perdu), contact, description
- Supprimer une opportunité (avec confirmation)
- Export CSV de la vue tableau
- Notification webhook n8n automatique quand un deal passe à `gagne`

Statuts disponibles :

| Statut | Signification |
|---|---|
| `prospect` | Identifié, pas encore contacté |
| `contacte` | Premier contact établi |
| `en_discussion` | Négociation en cours |
| `gagne` | Deal signé |
| `perdu` | Deal perdu |
| `en_pause` | En attente |

### Interactions (`pages/interactions.py`)

- Sélectionner une opportunité dans la liste
- Résumé de l'opportunité (deal, entreprise, montant, probabilité, statut, contact, relance)
- **Changer le statut** et la probabilité de l'opportunité (avec date de closing pour gagne/perdu)
- **Logger une interaction** : appel, email, RDV, LinkedIn, courrier
  - Champs : type, date, notes, prochain RDV/relance, par qui
  - Met à jour automatiquement la date de relance sur l'opportunité
- **Historique** des échanges (du plus récent au plus ancien)

---

## Modèle de données Supabase

### Table `entreprise`

| Colonne | Type | Description |
|---|---|---|
| `id` | uuid PK | Identifiant |
| `nom` | varchar | Nom de l'entreprise |
| `secteur` | varchar | Secteur d'activité |
| `ville` | varchar | Ville |
| `code_postal` | varchar | Code postal |
| `taille` | varchar | TPE / PME / ETI / GE / ASSOCIATION / FONDATION |
| `telephone` | varchar | Téléphone |
| `site_web` | varchar | URL du site |
| `notes` | text | Notes libres |

### Table `contact`

| Colonne | Type | Description |
|---|---|---|
| `id` | uuid PK | Identifiant |
| `entreprise_id` | uuid FK | Référence entreprise |
| `prenom` | varchar | Prénom |
| `nom` | varchar | Nom |
| `poste` | varchar | Intitulé du poste |
| `email` | varchar | Email |
| `telephone` | varchar | Téléphone |
| `linkedin_url` | varchar | Profil LinkedIn |
| `principal` | bool | Contact principal de l'entreprise |

### Table `opportunite`

| Colonne | Type | Description |
|---|---|---|
| `id` | uuid PK | Identifiant |
| `entreprise_id` | uuid FK | Référence entreprise |
| `contact_id` | uuid FK | Référence contact (obligatoire) |
| `titre` | varchar | Nom du deal |
| `montant_vise` | numeric | Montant en € |
| `statut` | varchar | Voir tableau statuts ci-dessus |
| `probabilite` | integer | 0–100 % |
| `date_relance` | date | Prochaine relance |
| `date_closing` | date | Date de clôture (gagne/perdu) |
| `description` | text | Description de l'offre |

### Table `interaction`

| Colonne | Type | Description |
|---|---|---|
| `id` | uuid PK | Identifiant |
| `opportunite_id` | uuid FK | Référence opportunité |
| `type` | varchar | appel / email / rdv / linkedin / courrier |
| `date` | date | Date de l'échange |
| `notes` | text | Compte-rendu |
| `prochain_rdv` | date | Prochaine échéance |
| `cree_par` | varchar | Auteur de la note |

---

## Intégration n8n (optionnel)

Quand un deal passe au statut `gagne`, l'application envoie automatiquement un POST HTTP vers `N8N_WEBHOOK_URL` avec le payload :

```json
{
  "opportunite_id": "...",
  "titre": "Sponsor maillot",
  "entreprise": "Acme Corp",
  "montant": 5000.0
}
```

Si le webhook est injoignable, un avertissement s'affiche mais le statut est quand même mis à jour.

### Commandes PM2 pour n8n

```bash
pm2 status          # voir si n8n tourne
pm2 logs n8n        # logs en direct
pm2 stop n8n        # arrêter n8n
pm2 restart n8n     # redémarrer n8n
```
