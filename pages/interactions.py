import streamlit as st
import db

st.set_page_config(page_title="Interactions", page_icon="💬", layout="wide")

st.title("Interactions")

# ─────────────────────────────────────────
# SÉLECTION DE L'OPPORTUNITÉ
# ─────────────────────────────────────────

opps = db.get_opportunites()

if not opps:
    st.info("Aucune opportunité pour l'instant. Crée d'abord des entreprises et des opportunités.")
    st.stop()

# Construire le selectbox
statut_colors = {
    "prospect":     "🔵",
    "contacte":     "🟡",
    "en_discussion":"🟠",
    "gagne":        "🟢",
    "perdu":        "🔴",
    "en_pause":     "⚪",
}

opp_options = {}
for o in opps:
    entreprise = o.get("entreprise") or {}
    nom_e = entreprise.get("nom", "—") if isinstance(entreprise, dict) else "—"
    emoji = statut_colors.get(o["statut"], "⚪")
    label = f"{emoji} {o['titre']} — {nom_e} ({o['statut']})"
    opp_options[label] = o

choix_label = st.selectbox("Sélectionne une opportunité", list(opp_options.keys()))
opp = opp_options[choix_label]

st.divider()

# ─────────────────────────────────────────
# RÉSUMÉ DE L'OPPORTUNITÉ
# ─────────────────────────────────────────

contact = opp.get("contact") or {}
nom_contact = f"{contact.get('prenom','')} {contact.get('nom','')}".strip() if isinstance(contact, dict) else "—"
entreprise  = opp.get("entreprise") or {}
nom_e       = entreprise.get("nom", "—") if isinstance(entreprise, dict) else "—"

with st.container(border=True):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Deal", opp["titre"])
    c2.metric("Entreprise", nom_e)
    c3.metric("Montant", f"{float(opp['montant_vise'] or 0):,.0f} €")
    c4.metric("Probabilité", f"{opp['probabilite']} %")

    cc1, cc2, cc3 = st.columns(3)
    emoji = statut_colors.get(opp["statut"], "⚪")
    cc1.markdown(f"**Statut :** {emoji} {opp['statut']}")
    cc2.markdown(f"**Contact :** {nom_contact}")
    cc3.markdown(f"**Relance :** {opp.get('date_relance','—')}")

# ─────────────────────────────────────────
# CHANGER LE STATUT
# ─────────────────────────────────────────

with st.expander("Changer le statut de l'opportunité"):
    statuts = ["prospect", "contacte", "en_discussion", "gagne", "perdu", "en_pause"]
    idx = statuts.index(opp["statut"]) if opp["statut"] in statuts else 0
    nouveau_statut = st.selectbox("Nouveau statut", statuts, index=idx, key="new_statut")
    nouvelle_proba = st.slider("Probabilité (%)", 0, 100, int(opp["probabilite"] or 0))

    if st.button("Mettre à jour le statut", type="primary"):
        db.update_opportunite(opp["id"], {
            "statut":      nouveau_statut,
            "probabilite": nouvelle_proba,
        })

        # Si deal gagné → appeler le webhook n8n
        if nouveau_statut == "gagne":
            import requests
            try:
                requests.post(
                    "http://localhost:5678/webhook/deal-gagne",
                    json={
                        "opportunite_id": opp["id"],
                        "titre":          opp["titre"],
                        "entreprise":     nom_e,
                        "montant":        float(opp["montant_vise"] or 0),
                    },
                    timeout=5
                )
            except Exception:
                pass  # n8n pas dispo, pas grave

        st.success(f"Statut mis à jour → {nouveau_statut}")
        st.rerun()

st.divider()

# ─────────────────────────────────────────
# LOGGER UNE INTERACTION
# ─────────────────────────────────────────

st.subheader("Logger une interaction")

with st.form("form_interaction"):
    c1, c2 = st.columns(2)
    type_inter  = c1.selectbox("Type", ["appel", "email", "rdv", "linkedin", "courrier"])
    date_inter  = c2.date_input("Date de l'échange")
    notes       = st.text_area("Notes / compte-rendu *", height=120,
                               placeholder="Ce qui a été dit, les points importants...")
    prochain    = c1.date_input("Prochain RDV / relance")
    cree_par    = c2.text_input("Par qui", placeholder="Ex: Thomas (président)")

    submitted = st.form_submit_button("Enregistrer l'interaction", type="primary")
    if submitted:
        if not notes:
            st.error("Les notes sont obligatoires.")
        else:
            db.create_interaction({
                "opportunite_id": opp["id"],
                "type":           type_inter,
                "date":           date_inter.isoformat(),
                "notes":          notes,
                "prochain_rdv":   prochain.isoformat(),
                "cree_par":       cree_par or "—",
            })
            # Mettre à jour la date de relance sur l'opportunité
            db.update_opportunite(opp["id"], {
                "date_relance":  prochain.isoformat(),
                "mis_a_jour_le": "now()",
            })
            st.success("Interaction enregistrée et date de relance mise à jour !")
            st.rerun()

st.divider()

# ─────────────────────────────────────────
# HISTORIQUE
# ─────────────────────────────────────────

st.subheader(" Historique des échanges")

interactions = db.get_interactions(opportunite_id=opp["id"])

if not interactions:
    st.info("Aucun échange enregistré pour cette opportunité.")
else:
    type_icons = {
        "appel":    "📞",
        "email":    "📧",
        "rdv":      "🤝",
        "linkedin": "💼",
        "courrier": "✉️",
    }
    for inter in interactions:
        icon = type_icons.get(inter["type"], "💬")
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 5, 2])
            c1.markdown(f"## {icon}")
            with c2:
                st.markdown(f"**{inter['type'].capitalize()}** — {inter['date']}")
                st.markdown(inter["notes"])
            with c3:
                if inter.get("prochain_rdv"):
                    st.caption(f"Prochain RDV : {inter['prochain_rdv']}")
                if inter.get("cree_par"):
                    st.caption(f"Par : {inter['cree_par']}")