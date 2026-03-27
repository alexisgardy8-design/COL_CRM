import streamlit as st


def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Plus+Jakarta+Sans:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* ── Titres — hiérarchie aérée, espacement horizontal ouvert ── */
    h1, h2, h3 {
        font-family: 'Syne', sans-serif !important;
        color: #0F172A !important;
    }
    h1 {
        font-size: 1.55rem !important;
        font-weight: 800 !important;
        line-height: 1.3 !important;
        letter-spacing: 0.01em !important;
        margin-top: 0.1rem !important;
        margin-bottom: 0.55rem !important;
    }
    h2 {
        font-size: 1.2rem !important;
        font-weight: 700 !important;
        line-height: 1.3 !important;
        letter-spacing: 0em !important;
        margin-top: 0.05rem !important;
        margin-bottom: 0.45rem !important;
        color: #1E293B !important;
    }
    h3 {
        font-size: 1.0rem !important;
        font-weight: 700 !important;
        line-height: 1.35 !important;
        letter-spacing: 0.01em !important;
        margin-top: 0 !important;
        margin-bottom: 0.35rem !important;
        color: #1E293B !important;
    }
    /* Responsive mobile */
    @media (max-width: 640px) {
        h1 { font-size: 1.3rem !important; letter-spacing: 0em !important; }
        h2 { font-size: 1.05rem !important; }
        h3 { font-size: 0.9rem !important; }
    }

    /* ── Sidebar sombre ── */
    section[data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 1px solid #1E293B !important;
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] li,
    section[data-testid="stSidebar"] a {
        color: #94A3B8 !important;
    }
    section[data-testid="stSidebar"] a:hover span {
        color: #F1F5F9 !important;
    }
    section[data-testid="stSidebarNavLink"][aria-current="page"] span {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    /* ── Metric cards ── */
    div[data-testid="stMetric"] {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-left: 3px solid #16A34A;
        border-radius: 8px;
        padding: 0.85rem 1.1rem !important;
    }
    div[data-testid="stMetricLabel"] p {
        font-size: 0.68rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.07em !important;
        color: #64748B !important;
    }
    div[data-testid="stMetricValue"] {
        font-family: 'Syne', sans-serif !important;
        font-weight: 700 !important;
        color: #0F172A !important;
    }

    /* ── Boutons primary ── */
    .stButton button[kind="primaryFormSubmit"],
    .stButton button[kind="primary"] {
        background-color: #16A34A !important;
        color: #fff !important;
        border: none !important;
        border-radius: 6px !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 600 !important;
        transition: all 0.15s ease !important;
    }
    .stButton button[kind="primaryFormSubmit"]:hover,
    .stButton button[kind="primary"]:hover {
        background-color: #15803D !important;
        box-shadow: 0 4px 12px rgba(22,163,74,0.28) !important;
        transform: translateY(-1px) !important;
    }

    /* ── Boutons secondaires ── */
    .stButton button {
        border-radius: 6px !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 500 !important;
        transition: all 0.15s ease !important;
    }

    /* ── Containers avec bordure ── */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 10px !important;
        border-color: #E2E8F0 !important;
        transition: box-shadow 0.18s ease !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        box-shadow: 0 3px 14px rgba(15,23,42,0.07) !important;
    }

    /* ── Inputs ── */
    input[type="text"], textarea {
        border-radius: 6px !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    /* ── Selectbox ── */
    div[data-baseweb="select"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    /* ── Divider ── */
    hr { border-color: #E2E8F0 !important; }

    /* ── Caption ── */
    small, .stCaption { color: #64748B !important; }

    /* ── Expander ── */
    details summary {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 600 !important;
    }
    </style>
    """, unsafe_allow_html=True)
