import streamlit as st
import pandas as pd
import requests
from datetime import date
import db
import utils

st.set_page_config(page_title="Opportunités", page_icon="🎯", layout="wide")
utils.inject_css()

st.title(" Opportunités — Pipeline")

# ─────────────────────────────────────────
# FILTRES
# ─────────────────────────────────────────

statut_colors = {
    "prospect":      "🔵",
    "contacte":      "🟡",
    "en_discussion": "🟠",
    "gagne":         "🟢",
    "perdu":         "🔴",
    "en_pause":      "⚪",
}

statuts_tous = ["Tous", "prospect", "contacte", "en_discussion", "gagne", "perdu", "en_pause"]

c1, c2, c3 = st.columns(3)
filtre_statut  = c1.selectbox("Statut", statuts_tous)
filtre_search  = c2.text_input(" Rechercher", placeholder="Titre, entreprise...")
filtre_sort    = c3.selectbox("Trier par", ["Date relance", "Montant (desc)", "Probabilité (desc)"])

# ─────────────────────────────────────────
# DONNÉES
# ─────────────────────────────────────────

opps = db.get_opportunites(statut=None if filtre_statut == "Tous" else filtre_statut)
tous_contacts = db.get_contacts()

if not opps:
    st.info("Aucune opportunité pour l'instant.")
    st.stop()

# Filtrage recherche
if filtre_search:
    opps = [
        o for o in opps
        if filtre_search.lower() in (o.get("titre") or "").lower()
        or filtre_search.lower() in ((o.get("entreprise") or {}).get("nom") or "").lower()
    ]

# Tri
if filtre_sort == "Montant (desc)":
    opps = sorted(opps, key=lambda x: float(x.get("montant_vise") or 0), reverse=True)
elif filtre_sort == "Probabilité (desc)":
    opps = sorted(opps, key=lambda x: int(x.get("probabilite") or 0), reverse=True)
else:
    opps = sorted(opps, key=lambda x: x.get("date_relance") or "9999-12-31")

st.divider()

# ─────────────────────────────────────────
# KPIs FILTRÉS
# ─────────────────────────────────────────

total    = sum(float(o.get("montant_vise") or 0) for o in opps if o["statut"] not in ["perdu"])
pondere  = sum(
    float(o.get("montant_vise") or 0) * int(o.get("probabilite") or 0) / 100
    for o in opps if o["statut"] not in ["perdu"]
)

k1, k2, k3 = st.columns(3)
k1.metric("Opportunités affichées", len(opps))
k2.metric("Pipeline total", f"{total:,.0f} €")
k3.metric("Pipeline pondéré", f"{pondere:,.0f} €")

st.divider()

# ─────────────────────────────────────────
# VUE KANBAN (cards par statut)
# ─────────────────────────────────────────

vue = st.radio("Vue", ["Cards", "Tableau"], horizontal=True)

if vue == "Cards":
    statuts_actifs = ["prospect", "contacte", "en_discussion", "gagne", "perdu", "en_pause"]
    if filtre_statut != "Tous":
        statuts_actifs = [filtre_statut]

    for statut in statuts_actifs:
        opps_statut = [o for o in opps if o["statut"] == statut]
        if not opps_statut:
            continue

        emoji = statut_colors[statut]
        montant_statut = sum(float(o.get("montant_vise") or 0) for o in opps_statut)
        st.markdown(f"### {emoji} {statut.replace('_',' ').capitalize()} — {len(opps_statut)} deal(s) · {montant_statut:,.0f} €")

        cols = st.columns(min(len(opps_statut), 3))
        for i, o in enumerate(opps_statut):
            col = cols[i % 3]
            entreprise = o.get("entreprise") or {}
            contact    = o.get("contact") or {}
            nom_e = entreprise.get("nom", "—") if isinstance(entreprise, dict) else "—"
            nom_c = f"{contact.get('prenom','')} {contact.get('nom','')}".strip() if isinstance(contact, dict) else "—"

            with col:
                with st.container(border=True):
                    st.markdown(f"**{o['titre']}**")
                    st.caption(f" {nom_e}")
                    st.caption(f" {nom_c}")
                    st.markdown(f"**{float(o.get('montant_vise') or 0):,.0f} €** · {o.get('probabilite',0)} %")
                    if o.get("date_relance"):
                        relance = o["date_relance"]
                        aujourd_hui = date.today().isoformat()
                        if relance < aujourd_hui:
                            st.caption(f"🔴 Relance : {relance} (en retard)")
                        elif relance == aujourd_hui:
                            st.caption(f"🟠 Relance : {relance} (aujourd'hui)")
                        else:
                            st.caption(f"🟢 Relance : {relance}")

                    # Actions rapides
                    ca, cb = st.columns(2)
                    with ca:
                        nouveaux_statuts = [s for s in statuts_tous[1:] if s != statut]
                        nouveau = st.selectbox(
                            "→ Statut",
                            nouveaux_statuts,
                            key=f"sel_{o['id']}",
                            label_visibility="collapsed"
                        )
                    with cb:
                        if st.button("Changer", key=f"btn_{o['id']}"):
                            db.update_opportunite(o["id"], {"statut": nouveau})
                            if nouveau == "gagne":
                                try:
                                    requests.post(
                                        db.N8N_WEBHOOK_URL,
                                        json={
                                            "opportunite_id": o["id"],
                                            "titre":          o["titre"],
                                            "entreprise":     nom_e,
                                            "montant":        float(o.get("montant_vise") or 0),
                                        },
                                        timeout=5
                                    )
                                except Exception:
                                    st.warning("Statut mis à jour, mais n8n n'a pas pu être notifié (webhook injoignable).")
                            st.rerun()

                    if st.button("Supprimer", key=f"del_{o['id']}"):
                        st.session_state[f"confirm_del_{o['id']}"] = True

                    if st.session_state.get(f"confirm_del_{o['id']}"):
                        st.warning("Confirmer la suppression ?")
                        d1, d2 = st.columns(2)
                        if d1.button("Oui", key=f"yes_{o['id']}", type="primary"):
                            db.delete_opportunite(o["id"])
                            st.rerun()
                        if d2.button("Non", key=f"no_{o['id']}"):
                            st.session_state[f"confirm_del_{o['id']}"] = False
                            st.rerun()

                    # Modifier opportunité
                    if st.button("Modifier", key=f"edit_{o['id']}"):
                        st.session_state[f"editing_opp_{o['id']}"] = True

                    if st.session_state.get(f"editing_opp_{o['id']}"):
                        contacts_opp = [
                            c for c in tous_contacts
                            if c.get("entreprise_id") == o.get("entreprise_id")
                        ]
                        with st.form(f"form_edit_opp_{o['id']}"):
                            st.markdown("**Modifier l'opportunité**")
                            fe1, fe2 = st.columns(2)
                            titre_e   = fe1.text_input("Titre *", value=o.get("titre",""))
                            montant_e = fe2.number_input(
                                "Montant (€)", min_value=0.0, step=100.0,
                                value=float(o.get("montant_vise") or 0)
                            )
                            statuts_list = ["prospect","contacte","en_discussion","gagne","perdu","en_pause"]
                            statut_idx   = statuts_list.index(o.get("statut","prospect"))
                            statut_e  = fe1.selectbox("Statut", statuts_list, index=statut_idx)
                            proba_e   = fe2.slider("Probabilité (%)", 0, 100, int(o.get("probabilite") or 0))
                            relance_val = date.fromisoformat(o["date_relance"]) if o.get("date_relance") else date.today()
                            relance_e = fe1.date_input("Date de relance", value=relance_val)
                            closing_e = None
                            if statut_e in ["gagne", "perdu"]:
                                closing_val = date.fromisoformat(o["date_closing"]) if o.get("date_closing") else date.today()
                                closing_e = fe2.date_input("Date de closing", value=closing_val)
                            # Contact — clé avec discriminant UUID pour éviter les homonymes
                            contact_opts = {
                                f"{c['prenom']} {c['nom']} ({c['id'][:8]})": c["id"]
                                for c in contacts_opp
                            }
                            new_contact_id = o.get("contact_id")
                            if contact_opts:
                                ct_labels = list(contact_opts.keys())
                                ct_ids    = list(contact_opts.values())
                                idx_ct    = ct_ids.index(new_contact_id) if new_contact_id in ct_ids else 0
                                choix_ct  = st.selectbox("Contact *", ct_labels, index=idx_ct)
                                new_contact_id = contact_opts[choix_ct]
                            else:
                                st.warning("Aucun contact disponible pour cette entreprise.")
                            desc_e = st.text_area("Description", value=o.get("description",""))
                            ef1, ef2 = st.columns(2)
                            if ef1.form_submit_button("Sauvegarder", type="primary"):
                                if not titre_e:
                                    st.error("Le titre est obligatoire.")
                                else:
                                    payload = {
                                        "titre":        titre_e,
                                        "montant_vise": montant_e,
                                        "statut":       statut_e,
                                        "probabilite":  proba_e,
                                        "date_relance": relance_e.isoformat(),
                                        "description":  desc_e or None,
                                        "contact_id":   new_contact_id,
                                    }
                                    if closing_e:
                                        payload["date_closing"] = closing_e.isoformat()
                                    db.update_opportunite(o["id"], payload)
                                    st.session_state[f"editing_opp_{o['id']}"] = False
                                    st.rerun()
                            if ef2.form_submit_button("Annuler"):
                                st.session_state[f"editing_opp_{o['id']}"] = False
                                st.rerun()

        st.divider()

# ─────────────────────────────────────────
# VUE TABLEAU
# ─────────────────────────────────────────

else:
    rows = []
    for o in opps:
        entreprise = o.get("entreprise") or {}
        contact    = o.get("contact") or {}
        nom_e = entreprise.get("nom", "—") if isinstance(entreprise, dict) else "—"
        nom_c = f"{contact.get('prenom','')} {contact.get('nom','')}".strip() if isinstance(contact, dict) else "—"
        rows.append({
            "Deal":         o["titre"],
            "Entreprise":   nom_e,
            "Contact":      nom_c,
            "Statut":       f"{statut_colors.get(o['statut'],'⚪')} {o['statut']}",
            "Montant (€)":  float(o.get("montant_vise") or 0),
            "Proba (%)":    int(o.get("probabilite") or 0),
            "Pondéré (€)":  float(o.get("montant_vise") or 0) * int(o.get("probabilite") or 0) / 100,
            "Relance":      o.get("date_relance", "—"),
            "Closing":      o.get("date_closing", "—"),
        })

    df = pd.DataFrame(rows)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Montant (€)":  st.column_config.NumberColumn(format="%.0f €"),
            "Pondéré (€)":  st.column_config.NumberColumn(format="%.0f €"),
            "Proba (%)":    st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d%%"),
        }
    )

    # Export CSV
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Exporter en CSV",
        data=csv,
        file_name="pipeline.csv",
        mime="text/csv"
    )