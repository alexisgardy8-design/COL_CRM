import streamlit as st
import db

st.set_page_config(page_title="Entreprises", page_icon="🏢", layout="wide")

st.title("Entreprises")

# ─────────────────────────────────────────
# FORMULAIRE AJOUT
# ─────────────────────────────────────────

with st.expander(" Ajouter une entreprise", expanded=False):
    with st.form("form_entreprise"):
        c1, c2 = st.columns(2)
        nom         = c1.text_input("Nom *")
        secteur     = c2.text_input("Secteur (ex: Alimentation, Auto...)")
        ville       = c1.text_input("Ville")
        code_postal = c2.text_input("Code postal")
        taille      = c1.selectbox("Taille", ["TPE", "PME", "ETI", "GE"])
        site_web    = c2.text_input("Site web")
        telephone   = c1.text_input("Téléphone")
        notes       = st.text_area("Notes")

        submitted = st.form_submit_button("Enregistrer", type="primary")
        if submitted:
            if not nom:
                st.error("Le nom est obligatoire.")
            else:
                db.create_entreprise({
                    "nom":         nom,
                    "secteur":     secteur or None,
                    "ville":       ville or None,
                    "code_postal": code_postal or None,
                    "taille":      taille,
                    "site_web":    site_web or None,
                    "telephone":   telephone or None,
                    "notes":       notes or None,
                })
                st.success(f" {nom} ajoutée !")
                st.rerun()

st.divider()

# ─────────────────────────────────────────
# LISTE DES ENTREPRISES
# ─────────────────────────────────────────

entreprises = db.get_entreprises()

if not entreprises:
    st.info("Aucune entreprise pour l'instant. Ajoutes-en une ci-dessus.")
    st.stop()

# Recherche
search = st.text_input(" Rechercher", placeholder="Nom, ville, secteur...")
if search:
    entreprises = [
        e for e in entreprises
        if search.lower() in (e.get("nom") or "").lower()
        or search.lower() in (e.get("ville") or "").lower()
        or search.lower() in (e.get("secteur") or "").lower()
    ]

st.caption(f"{len(entreprises)} entreprise(s)")

# ─────────────────────────────────────────
# CARDS
# ─────────────────────────────────────────

for e in entreprises:
    with st.container(border=True):
        c1, c2, c3 = st.columns([4, 3, 2])

        with c1:
            st.markdown(f"### {e['nom']}")
            if e.get("secteur"):
                st.caption(e["secteur"])

        with c2:
            if e.get("ville"):
                st.markdown(f" {e['ville']} {e.get('code_postal','')}")
            if e.get("telephone"):
                st.markdown(f" {e['telephone']}")
            if e.get("site_web"):
                st.markdown(f" [{e['site_web']}]({e['site_web']})")

        with c3:
            st.caption(f"Taille : {e.get('taille','—')}")

            # Contacts liés
            contacts = db.get_contacts(entreprise_id=e["id"])
            st.caption(f" {len(contacts)} contact(s)")

            # Opportunités liées
            opps = db.get_opportunites()
            opps_entreprise = [o for o in opps if o.get("entreprise_id") == e["id"]]
            st.caption(f" {len(opps_entreprise)} opportunité(s)")

        # Notes
        if e.get("notes"):
            st.caption(f" {e['notes']}")

        # Actions
        col_edit, col_del, col_opp, col_contact = st.columns([1, 1, 2, 2])

        # Modifier
        with col_edit:
            if st.button("Modifier", key=f"edit_{e['id']}"):
                st.session_state[f"editing_{e['id']}"] = True

        # Supprimer
        with col_del:
            if st.button("Supprimer", key=f"del_{e['id']}"):
                st.session_state[f"confirm_del_{e['id']}"] = True

        if st.session_state.get(f"confirm_del_{e['id']}"):
            st.warning(f"Supprimer **{e['nom']}** et tous ses contacts / opportunités ?")
            cc1, cc2 = st.columns(2)
            if cc1.button("Oui, supprimer", key=f"yes_{e['id']}", type="primary"):
                db.delete_entreprise(e["id"])
                st.success("Supprimé.")
                st.rerun()
            if cc2.button("Annuler", key=f"no_{e['id']}"):
                st.session_state[f"confirm_del_{e['id']}"] = False
                st.rerun()

        # Ajouter un contact
        with col_contact:
            if st.button(f"Ajouter contact", key=f"contact_{e['id']}"):
                st.session_state[f"add_contact_{e['id']}"] = True

        # Ajouter une opportunité
        with col_opp:
            if st.button(f"Ajouter opportunité", key=f"opp_{e['id']}"):
                st.session_state[f"add_opp_{e['id']}"] = True

        # ── Formulaire modification ──
        if st.session_state.get(f"editing_{e['id']}"):
            with st.form(f"form_edit_{e['id']}"):
                st.markdown("**Modifier l'entreprise**")
                c1, c2 = st.columns(2)
                nom_e     = c1.text_input("Nom", value=e.get("nom",""))
                secteur_e = c2.text_input("Secteur", value=e.get("secteur",""))
                ville_e   = c1.text_input("Ville", value=e.get("ville",""))
                cp_e      = c2.text_input("Code postal", value=e.get("code_postal",""))
                taille_e  = c1.selectbox("Taille", ["TPE","PME","ETI","GE"],
                                index=["TPE","PME","ETI","GE"].index(e.get("taille","TPE")))
                tel_e     = c2.text_input("Téléphone", value=e.get("telephone",""))
                web_e     = c1.text_input("Site web", value=e.get("site_web",""))
                notes_e   = st.text_area("Notes", value=e.get("notes",""))
                s1, s2 = st.columns(2)
                if s1.form_submit_button("Sauvegarder", type="primary"):
                    db.update_entreprise(e["id"], {
                        "nom": nom_e, "secteur": secteur_e,
                        "ville": ville_e, "code_postal": cp_e,
                        "taille": taille_e, "telephone": tel_e,
                        "site_web": web_e, "notes": notes_e,
                    })
                    st.session_state[f"editing_{e['id']}"] = False
                    st.rerun()
                if s2.form_submit_button("Annuler"):
                    st.session_state[f"editing_{e['id']}"] = False
                    st.rerun()

        # ── Formulaire ajout contact ──
        if st.session_state.get(f"add_contact_{e['id']}"):
            with st.form(f"form_contact_{e['id']}"):
                st.markdown("**Nouveau contact**")
                c1, c2 = st.columns(2)
                prenom  = c1.text_input("Prénom *")
                nom_c   = c2.text_input("Nom *")
                poste   = c1.text_input("Poste")
                email   = c2.text_input("Email")
                tel_c   = c1.text_input("Téléphone")
                linkedin= c2.text_input("LinkedIn URL")
                principal = st.checkbox("Contact principal", value=True)
                s1, s2 = st.columns(2)
                if s1.form_submit_button("Ajouter", type="primary"):
                    if not prenom or not nom_c:
                        st.error("Prénom et nom obligatoires.")
                    else:
                        db.create_contact({
                            "entreprise_id": e["id"],
                            "prenom": prenom, "nom": nom_c,
                            "poste": poste or None,
                            "email": email or None,
                            "telephone": tel_c or None,
                            "linkedin_url": linkedin or None,
                            "principal": principal,
                        })
                        st.session_state[f"add_contact_{e['id']}"] = False
                        st.rerun()
                if s2.form_submit_button("Annuler"):
                    st.session_state[f"add_contact_{e['id']}"] = False
                    st.rerun()

        # ── Formulaire ajout opportunité ──
        if st.session_state.get(f"add_opp_{e['id']}"):
            contacts_e = db.get_contacts(entreprise_id=e["id"])
            with st.form(f"form_opp_{e['id']}"):
                st.markdown("**Nouvelle opportunité**")
                c1, c2 = st.columns(2)
                titre    = c1.text_input("Titre * (ex: Sponsor maillot)")
                montant  = c2.number_input("Montant visé (€)", min_value=0.0, step=100.0)
                statut   = c1.selectbox("Statut", ["prospect","contacte","en_discussion","gagne","perdu","en_pause"])
                proba    = c2.slider("Probabilité (%)", 0, 100, 50)
                relance  = c1.date_input("Date de relance")
                closing  = c2.date_input("Date closing")
                contact_options = {f"{c['prenom']} {c['nom']}": c["id"] for c in contacts_e}
                contact_choisi = None
                if contact_options:
                    choix = st.selectbox("Contact", list(contact_options.keys()))
                    contact_choisi = contact_options[choix]
                description = st.text_area("Description de l'offre")
                s1, s2 = st.columns(2)
                if s1.form_submit_button("Ajouter", type="primary"):
                    if not titre:
                        st.error("Le titre est obligatoire.")
                    else:
                        db.create_opportunite({
                            "entreprise_id": e["id"],
                            "contact_id":    contact_choisi,
                            "titre":         titre,
                            "montant_vise":  montant,
                            "statut":        statut,
                            "probabilite":   proba,
                            "date_relance":  relance.isoformat(),
                            "date_closing":  closing.isoformat(),
                            "description":   description or None,
                        })
                        st.session_state[f"add_opp_{e['id']}"] = False
                        st.rerun()
                if s2.form_submit_button("Annuler"):
                    st.session_state[f"add_opp_{e['id']}"] = False
                    st.rerun()