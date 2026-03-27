import streamlit as st
import pandas as pd
import db
import utils

st.set_page_config(
    page_title="CRM Club Olympique de Lutèce",
    page_icon="⚽",
    layout="wide"
)
utils.inject_css()

st.title("CRM — Prospection Partenaires")

# ─────────────────────────────────────────
# KPIs
# ─────────────────────────────────────────

kpis = db.get_kpis()

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    label="Prospects actifs",
    value=kpis["total_prospects"],
    help="Opportunités hors deals gagnés/perdus"
)
col2.metric(
    label="Pipeline total",
    value=f"{kpis['pipeline_total']:,.0f} €"
)
col3.metric(
    label="Pipeline pondéré",
    value=f"{kpis['pipeline_pondere']:,.0f} €"
)
col4.metric(
    label="Deals gagnés",
    value=kpis["deals_gagnes"]
)
col5.metric(
    label="Montant gagné",
    value=f"{kpis['montant_gagne']:,.0f} €"
)

st.divider()

# ─────────────────────────────────────────
# RELANCES DU JOUR
# ─────────────────────────────────────────

st.subheader("Relances du jour")

relances = db.get_relances_du_jour()

if not relances:
    st.success("Aucune relance prévue aujourd'hui.")
else:
    for r in relances:
        entreprise = r.get("entreprise", {}) or {}
        contact    = r.get("contact", {}) or {}
        nom_entreprise = entreprise.get("nom", "—")
        nom_contact    = f"{contact.get('prenom', '')} {contact.get('nom', '')}".strip() or "—"

        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            c1.markdown(f"**{r['titre']}**  \n{nom_entreprise}")
            c2.markdown(f"Contact : {nom_contact}")
            c3.markdown(f"Montant : **{float(r['montant_vise'] or 0):,.0f} €** ({r['probabilite']} %)")
            with c4:
                statut_colors = {
                    "prospect":     "🔵",
                    "contacte":     "🟡",
                    "en_discussion":"🟠",
                    "gagne":        "🟢",
                    "perdu":        "🔴",
                    "en_pause":     "⚪",
                }
                emoji = statut_colors.get(r["statut"], "⚪")
                st.markdown(f"{emoji} {r['statut']}")

st.divider()

# ─────────────────────────────────────────
# PIPELINE PAR STATUT
# ─────────────────────────────────────────

st.subheader("📊 Pipeline par statut")

opps = db.get_opportunites()

if not opps:
    st.info("Aucune opportunité pour l'instant. Commence par ajouter des prospects.")
else:
    df = pd.DataFrame(opps)
    df["montant_vise"] = df["montant_vise"].astype(float)
    df["probabilite"]  = df["probabilite"].fillna(0).astype(int)
    df["montant_pondere"] = df["montant_vise"] * df["probabilite"] / 100

    # Tableau résumé par statut
    ordre_statuts = ["prospect", "contacte", "en_discussion", "gagne", "perdu", "en_pause"]
    resume = (
        df.groupby("statut")
        .agg(
            nb=("id", "count"),
            total=("montant_vise", "sum"),
            pondere=("montant_pondere", "sum")
        )
        .reindex([s for s in ordre_statuts if s in df["statut"].values])
        .reset_index()
    )
    resume.columns = ["Statut", "Nb deals", "Montant total (€)", "Montant pondéré (€)"]
    resume["Montant total (€)"]   = resume["Montant total (€)"].map("{:,.0f} €".format)
    resume["Montant pondéré (€)"] = resume["Montant pondéré (€)"].map("{:,.0f} €".format)

    st.dataframe(resume, use_container_width=True, hide_index=True)

    st.divider()

    # Dernières opportunités ajoutées
    st.subheader("Dernières opportunités ajoutées")

    df_display = df.copy()
    df_display["entreprise"] = df_display["entreprise"].apply(
        lambda x: x.get("nom", "—") if isinstance(x, dict) else "—"
    )
    df_display["contact"] = df_display["contact"].apply(
        lambda x: f"{x.get('prenom','')} {x.get('nom','')}".strip() if isinstance(x, dict) else "—"
    )
    df_display = df_display[[
        "titre", "entreprise", "contact",
        "montant_vise", "statut", "probabilite", "date_relance", "cree_le"
    ]].rename(columns={
        "titre":         "Deal",
        "entreprise":    "Entreprise",
        "contact":       "Contact",
        "montant_vise":  "Montant (€)",
        "statut":        "Statut",
        "probabilite":   "Proba (%)",
        "date_relance":  "Relance",
        "cree_le":       "_cree_le",
    }).sort_values("_cree_le", ascending=False).head(10).drop(columns=["_cree_le"])

    st.dataframe(df_display, use_container_width=True, hide_index=True)