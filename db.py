import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError(
        "Variables d'environnement manquantes : SUPABASE_URL et SUPABASE_KEY "
        "doivent être définies dans le fichier .env"
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# URL webhook n8n — modifiable via .env pour pointer vers un VPS en production
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/deal-gagne")


# ─────────────────────────────────────────
# ENTREPRISES
# ─────────────────────────────────────────

def get_entreprises():
    res = supabase.table("entreprise").select("*").order("nom").execute()
    return res.data

def get_entreprise(id: str):
    res = supabase.table("entreprise").select("*").eq("id", id).single().execute()
    return res.data

def create_entreprise(data: dict):
    res = supabase.table("entreprise").insert(data).execute()
    return res.data

def update_entreprise(id: str, data: dict):
    res = supabase.table("entreprise").update(data).eq("id", id).execute()
    return res.data

def delete_entreprise(id: str):
    res = supabase.table("entreprise").delete().eq("id", id).execute()
    return res.data


# ─────────────────────────────────────────
# CONTACTS
# ─────────────────────────────────────────

def get_contacts(entreprise_id: str = None):
    query = supabase.table("contact").select("*")
    if entreprise_id:
        query = query.eq("entreprise_id", entreprise_id)
    res = query.order("nom").execute()
    return res.data

def create_contact(data: dict):
    res = supabase.table("contact").insert(data).execute()
    return res.data

def update_contact(id: str, data: dict):
    res = supabase.table("contact").update(data).eq("id", id).execute()
    return res.data

def delete_contact(id: str):
    res = supabase.table("contact").delete().eq("id", id).execute()
    return res.data


# ─────────────────────────────────────────
# OPPORTUNITES
# ─────────────────────────────────────────

def get_opportunites(statut: str = None):
    query = supabase.table("opportunite").select(
        "*, entreprise(nom), contact(prenom, nom, email)"
    )
    if statut:
        query = query.eq("statut", statut)
    res = query.order("date_relance").execute()
    return res.data

def get_opportunite(id: str):
    res = supabase.table("opportunite").select(
        "*, entreprise(nom), contact(prenom, nom, email)"
    ).eq("id", id).single().execute()
    return res.data

def create_opportunite(data: dict):
    if not data.get("contact_id"):
        raise ValueError(
            "Impossible de créer une opportunité sans contact. "
            "Veuillez associer un contact à cette opportunité."
        )
    res = supabase.table("opportunite").insert(data).execute()
    return res.data

def update_opportunite(id: str, data: dict):
    res = supabase.table("opportunite").update(data).eq("id", id).execute()
    return res.data

def delete_opportunite(id: str):
    res = supabase.table("opportunite").delete().eq("id", id).execute()
    return res.data

def get_relances_du_jour():
    from datetime import date
    aujourd_hui = date.today().isoformat()
    res = supabase.table("opportunite").select(
        "*, entreprise(nom), contact(prenom, nom, email)"
    ).eq("date_relance", aujourd_hui).not_.in_("statut", ["gagne", "perdu"]).execute()
    return res.data


# ─────────────────────────────────────────
# INTERACTIONS
# ─────────────────────────────────────────

def get_interactions(opportunite_id: str):
    res = supabase.table("interactions").select("*").eq(
        "opportunite_id", opportunite_id
    ).order("date", desc=True).execute()
    return res.data

def create_interaction(data: dict):
    res = supabase.table("interactions").insert(data).execute()
    return res.data


# ─────────────────────────────────────────
# KPIs
# ─────────────────────────────────────────

def get_kpis():
    res = supabase.table("opportunite").select(
        "statut, montant_vise, probabilite"
    ).execute()
    data = res.data

    total_prospects  = sum(1 for r in data if r["statut"] not in ["gagne", "perdu"])
    pipeline_total   = sum(float(r["montant_vise"] or 0) for r in data if r["statut"] not in ["perdu"])
    pipeline_pondere = sum(
        float(r["montant_vise"] or 0) * (int(r["probabilite"] or 0) / 100)
        for r in data if r["statut"] not in ["perdu"]
    )
    deals_gagnes     = sum(1 for r in data if r["statut"] == "gagne")
    montant_gagne    = sum(float(r["montant_vise"] or 0) for r in data if r["statut"] == "gagne")

    return {
        "total_prospects":  total_prospects,
        "pipeline_total":   pipeline_total,
        "pipeline_pondere": pipeline_pondere,
        "deals_gagnes":     deals_gagnes,
        "montant_gagne":    montant_gagne,
    }