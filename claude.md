# CLAUDE.md — CRM Asso Foot

## Vue d'ensemble

CRM de prospection partenaires/sponsors pour une association de football.
Stack : Streamlit + Supabase + n8n + Git.

---

## Architecture

```
crm-asso/
├── app.py                  ← Dashboard KPIs + relances du jour (point d'entrée)
├── db.py                   ← Toutes les fonctions Supabase + constante N8N_WEBHOOK_URL
├── utils.py                ← inject_css() — appelé sur toutes les pages (design premium)
├── pages/
│   ├── entreprises.py      ← CRUD entreprises + contacts + création opportunités
│   ├── opportunites.py     ← Pipeline deals (vue cards + vue tableau + export CSV)
│   └── interactions.py     ← Log échanges + changement statut + historique
├── .env                    ← SUPABASE_URL + SUPABASE_KEY + N8N_WEBHOOK_URL (jamais commité)
├── .venv/                  ← Environnement Python isolé (jamais commité)
├── requirements.txt        ← streamlit, supabase, python-dotenv, pandas
└── .gitignore              ← .env, .venv/, __pycache__/, .streamlit/secrets.toml
```

---

## Base de données Supabase

### Tables

**entreprise**
- `id` uuid PK (gen_random_uuid())
- `nom` varchar
- `secteur` varchar
- `ville` varchar
- `code_postal` varchar — varchar pas int (ex: 01000)
- `taille` varchar — valeurs : TPE / PME / ETI / GE
- `site_web` varchar
- `telephone` varchar
- `notes` text
- `cree_le` timestamptz DEFAULT now()
- `mis_a_jour_le` timestamptz — mis à jour via trigger

**contact**
- `id` uuid PK
- `entreprise_id` uuid FK → entreprise.id (ON DELETE CASCADE)
- `prenom` varchar
- `nom` varchar
- `poste` varchar
- `email` varchar
- `telephone` varchar
- `linkedin_url` varchar
- `principal` bool — true = interlocuteur principal
- `cree_le` timestamptz DEFAULT now()

**opportunite**
- `id` uuid PK
- `entreprise_id` uuid FK → entreprise.id (ON DELETE CASCADE)
- `contact_id` uuid FK → contact.id (ON DELETE SET NULL) — SET NULL car deal survit au contact
- `titre` varchar
- `montant_vise` numeric — euros, 2 décimales
- `statut` varchar — prospect / contacte / en_discussion / gagne / perdu / en_pause
- `probabilite` integer — 0 à 100, sert au pipeline pondéré
- `date_relance` date — pilote les alertes n8n
- `date_closing` date — NULL à la création, rempli par n8n ou manuellement au closing
- `description` text
- `cree_le` timestamptz DEFAULT now()
- `mis_a_jour_le` timestamptz

**interaction**
- `id` uuid PK
- `opportunite_id` uuid FK → opportunite.id (ON DELETE CASCADE)
- `type` varchar — appel / email / rdv / linkedin / courrier
- `date` date
- `notes` text
- `prochain_rdv` date — remonte dans date_relance de l'opportunité
- `cree_par` varchar — nom du membre de l'asso
- `cree_le` timestamptz DEFAULT now()

### Règles FK

| FK | ON DELETE | ON UPDATE | Raison |
|---|---|---|---|
| contact.entreprise_id | CASCADE | CASCADE | Contact sans entreprise = orphelin |
| opportunite.entreprise_id | CASCADE | CASCADE | Opportunité sans entreprise = sans sens |
| opportunite.contact_id | SET NULL | CASCADE | Deal survit si contact supprimé |
| interaction.opportunite_id | CASCADE | CASCADE | Historique lié à l'opportunité |

### Sécurité

RLS désactivé sur toutes les tables (usage interne, pas d'auth utilisateur) :
```sql
ALTER TABLE entreprise  DISABLE ROW LEVEL SECURITY;
ALTER TABLE contact     DISABLE ROW LEVEL SECURITY;
ALTER TABLE opportunite DISABLE ROW LEVEL SECURITY;
ALTER TABLE interaction DISABLE ROW LEVEL SECURITY;
```

---

## db.py — Conventions

- Connexion Supabase via `anon key` (pas la service_role)
- Chargement des secrets via `python-dotenv` + fichier `.env`
- Une fonction par action CRUD, jamais de logique métier dans db.py
- Les jointures se font via PostgREST : `select("*, entreprise(nom), contact(prenom, nom)")`
- `get_relances_du_jour()` filtre sur `date_relance = today` et statut NOT IN gagne/perdu
- `get_kpis()` calcule pipeline_total, pipeline_pondéré (montant × proba/100), deals_gagnés
- `N8N_WEBHOOK_URL` : constante lue depuis `.env`, fallback sur `localhost:5678`
- Guard au démarrage : lève `EnvironmentError` si SUPABASE_URL ou SUPABASE_KEY absent

## utils.py — Conventions

- `inject_css()` : à appeler en début de chaque page après `st.set_page_config()`
- Injecte les fonts Google (Syne + Plus Jakarta Sans), sidebar sombre, metric cards stylisées
- Titres : h1=1.55rem, h2=1.2rem, h3=1.0rem — responsive mobile via media query
- Ne pas mettre de logique métier ou d'accès data dans ce fichier

## Sécurité — Points d'attention

- **RLS désactivé** sur Supabase : usage interne uniquement. Si déployé publiquement,
  activer l'auth Streamlit (`st.secrets`) et RLS avant tout.
- **Notes utilisateur** : rendues via `html.escape()` + `unsafe_allow_html=True`
  pour préserver les sauts de ligne sans risque XSS.
- **N8N_WEBHOOK_URL** : ne jamais commiter une URL avec token ou credential dedans.
- **Anon key Supabase** : ne pas la remplacer par la `service_role` key dans `.env`.

---

## n8n — Workflows

n8n tourne en local via pm2 sur `localhost:5678`.
Les workflows sont sauvegardés dans la base SQLite interne de n8n.

### Workflow 1 — Relances quotidiennes (automatique)

```
Schedule (8h00)
→ Supabase Get many rows
    table: opportunite
    filtres: date_relance eq {{ $now.format('yyyy-MM-dd') }}
             statut neq gagne
             statut neq perdu
→ IF items.length > 0
→ Loop Over Items
→ Gmail Send Email (rappel à ton adresse)
→ Supabase Create a row
    table: interaction
    type: email, notes: "Relance automatique envoyée", cree_par: "n8n (auto)"
```

### Workflow 2 — Deal gagné (déclenché par Streamlit)

```
Webhook POST /deal-gagne
→ Supabase Update a row
    table: opportunite
    select by: id = {{ $json.body.opportunite_id }}
    fields: statut = gagne, mis_a_jour_le = {{ $now }}, date_closing = {{ $now.format('yyyy-MM-dd') }}
→ Gmail Send Email (notif équipe)
→ Supabase Create a row
    table: interaction
    notes: "Deal marqué comme gagné"
```

Body attendu du POST Streamlit :
```json
{
  "opportunite_id": "uuid",
  "titre": "Sponsor maillot",
  "entreprise": "Boulangerie Durand",
  "montant": 1500.0
}
```

### Credentials n8n

- Supabase : Host = `https://xxxx.supabase.co` + service_role key
- Gmail : OAuth2 (Google Cloud Console, app en mode test, compte ajouté dans Audience)

---

## Streamlit — Conventions

### app.py (dashboard)

- 5 métriques : prospects actifs, pipeline total, pipeline pondéré, deals gagnés, montant gagné
- Relances du jour en cards avec couleur statut
- Tableau pipeline par statut + 10 dernières opportunités

### pages/entreprises.py

- Formulaire ajout entreprise dans un `st.expander`
- Recherche filtrante (nom, ville, secteur)
- Cards avec actions inline : modifier, supprimer, ajouter contact, ajouter opportunité
- `date_closing` absente du formulaire de création — toujours NULL à la création

### pages/opportunites.py

- Filtres : statut + recherche + tri
- Vue Cards : groupées par statut, changement statut inline, indicateur retard relance
- Vue Tableau : dataframe avec barre progression proba + export CSV
- Appel webhook n8n si statut → gagne

### pages/interactions.py

- Sélection de l'opportunité via selectbox
- Résumé de l'opportunité en métriques
- Changement statut : affiche `date_closing` uniquement si statut = gagne ou perdu
- Log interaction : met à jour `date_relance` de l'opportunité avec `prochain_rdv`
- Historique avec icônes par type d'interaction

---

## Variables d'environnement

```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJhbGci...         ← anon key (pas service_role)
N8N_WEBHOOK_URL=http://localhost:5678/webhook/deal-gagne  ← changer en HTTPS sur VPS
```

> `N8N_WEBHOOK_URL` est lue dans `db.py` et exposée comme `db.N8N_WEBHOOK_URL`.
> En production sur VPS, remplacer par l'URL publique HTTPS.

---

## Commandes utiles

```bash
# Activer le venv
source .venv/bin/activate

# Lancer Streamlit
streamlit run app.py

# Vérifier la connexion Supabase
python3 -c "import db; print(db.get_entreprises())"

# pm2 — n8n
pm2 start n8n --name "n8n"
pm2 status
pm2 logs n8n
pm2 restart n8n

# Git
git add .
git commit -m "feat: ..."
git push
```

---

## Ce qui reste à faire (évolutions possibles)

- Déployer Streamlit sur un VPS ou Streamlit Cloud
- Déployer n8n sur un VPS (remplacer localhost:5678 par l'URL publique dans les webhooks)
- Ajouter une authentification Streamlit (`st.secrets` + password simple)
- Workflow n8n : relance si aucune interaction depuis X jours
- Page Streamlit : import CSV de prospects en masse
- Tableau de bord : graphique évolution du pipeline dans le temps