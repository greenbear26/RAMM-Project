import logging
logging.basicConfig(format='%(filename)s:%(lineno)s:%(levelname)s -- %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

import os
import requests
import streamlit as st
from PIL import Image
from modules.nav import SideBarLinks

API_BASE = "http://web-api:4000"

_logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "Lobby_logo.png")
_logo_img  = Image.open(_logo_path)

st.set_page_config(layout='wide', page_title="LobbyLens", page_icon=_logo_img)

if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'saved_comparisons' not in st.session_state:
    st.session_state['saved_comparisons'] = []
if 'saved_orgs' not in st.session_state:
    st.session_state['saved_orgs'] = []
if 'compare_pair' not in st.session_state:
    st.session_state['compare_pair'] = []

SideBarLinks(show_home=True)
logger.info("Loading the Home page of the app")


@st.cache_data(ttl=300)
def fetch_users(role):
    try:
        resp = requests.get(f"{API_BASE}/users", params={"role": role}, timeout=3)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []


def user_label(u):
    ln = u.get("last_name") or ""
    return f"{u['first_name']} {ln}".strip()


citizens    = fetch_users("citizen")
researchers = fetch_users("researcher")
journalists = fetch_users("journalist")

citizen_options    = sorted(citizens,    key=lambda u: u.get("last_name") or "")
researcher_options = sorted(researchers, key=lambda u: u.get("last_name") or "")
journalist_options = sorted(journalists, key=lambda u: u.get("last_name") or "")

# Header
st.markdown("""
<div style="text-align: center; padding: 32px 0 20px 0;">
    <h1 style="color: #1A1A2E; font-size: 42px; font-weight: 800; margin: 0 0 6px 0;
               letter-spacing: -1px;">LobbyLens</h1>
    <p style="color: #4A6FA5; font-size: 15px; margin: 0 0 6px 0; font-weight: 600;">
        Transparency into EU Lobbying &amp; Political Influence
    </p>
    <p style="color: #64748B; font-size: 13px; margin: 0 auto; max-width: 480px;">
        Track lobbying spend, compare organizational influence, and uncover the forces behind EU decision-making.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<p style="text-align:center; color:#94A3B8; font-size:11px; letter-spacing:2px;
   text-transform:uppercase; font-weight:600; margin-bottom:14px;">
   Select your role to continue
</p>
""", unsafe_allow_html=True)

CARD_STYLE = """
background: #1E293B;
border: 1px solid #334155;
border-radius: 12px;
padding: 18px 18px 14px 18px;
margin-bottom: 10px;
height: 160px;
overflow: hidden;
"""

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f'<div style="{CARD_STYLE}"><h3 style="color:#FFFFFF; margin:0 0 4px 0; font-size:15px; font-weight:700;">European Citizen</h3><p style="color:#94A3B8; font-size:11px; line-height:1.5; margin:0;">Explore EU lobbying organizations and their different attributes.</p></div>', unsafe_allow_html=True)
    if citizen_options:
        selected_citizen = st.selectbox("Select citizen", citizen_options,
                                        format_func=user_label,
                                        key="citizen_select", label_visibility="collapsed")
        if st.button("Login as Citizen", key="citizen_login", type="primary", use_container_width=True):
            st.session_state['authenticated'] = True
            st.session_state['role'] = 'citizen'
            st.session_state['user_id'] = selected_citizen['user_id']
            st.session_state['first_name'] = selected_citizen['first_name']
            st.session_state['last_name'] = selected_citizen.get('last_name', '')
            logger.info(f"Logging in as Citizen: {user_label(selected_citizen)}")
            st.switch_page('pages/00_Citizen_Home.py')
    else:
        st.info("Could not load users — backend may be starting up.")

with c2:
    st.markdown(f'<div style="{CARD_STYLE}"><h3 style="color:#FFFFFF; margin:0 0 4px 0; font-size:15px; font-weight:700;">Political Science Researcher</h3><p style="color:#94A3B8; font-size:11px; line-height:1.5; margin:0;">Compare lobbying organizations and analyze their influence on the EU.</p></div>', unsafe_allow_html=True)
    if researcher_options:
        selected_researcher = st.selectbox("Select researcher", researcher_options,
                                           format_func=user_label,
                                           key="researcher_select", label_visibility="collapsed")
        if st.button("Login as Researcher", key="researcher_login", type="primary", use_container_width=True):
            st.session_state['authenticated'] = True
            st.session_state['role'] = 'researcher'
            st.session_state['user_id'] = selected_researcher['user_id']
            st.session_state['first_name'] = selected_researcher['first_name']
            st.session_state['last_name'] = selected_researcher.get('last_name', '')
            logger.info(f"Logging in as Researcher: {user_label(selected_researcher)}")
            st.switch_page('pages/10_Polysci_Home.py')
    else:
        st.info("Could not load users — backend may be starting up.")

with c3:
    st.markdown(f'<div style="{CARD_STYLE}"><h3 style="color:#FFFFFF; margin:0 0 4px 0; font-size:15px; font-weight:700;">Political Party Journalist</h3><p style="color:#94A3B8; font-size:11px; line-height:1.5; margin:0;">Track European political parties, their influence on national parliaments, and their interactions with lobbying organizations.</p></div>', unsafe_allow_html=True)
    if journalist_options:
        selected_journalist = st.selectbox("Select journalist", journalist_options,
                                           format_func=user_label,
                                           key="journalist_select", label_visibility="collapsed")
        if st.button("Login as Journalist", key="journalist_login", type="primary", use_container_width=True):
            st.session_state['authenticated'] = True
            st.session_state['role'] = 'journalist'
            st.session_state['user_id'] = selected_journalist['user_id']
            st.session_state['first_name'] = selected_journalist['first_name']
            st.session_state['last_name'] = selected_journalist.get('last_name', '')
            logger.info(f"Logging in as Journalist: {user_label(selected_journalist)}")
            st.switch_page('pages/20_Journalist_Home.py')
    else:
        st.info("Could not load users — backend may be starting up.")

st.markdown("""
<div style="margin-top: 32px; text-align: center; color: #94A3B8; font-size: 11px;">
    LobbyLens &nbsp;·&nbsp; EU Lobbying Transparency Platform &nbsp;·&nbsp;
    Data sourced from the EU Transparency Register &amp; LobbyFacts
</div>
""", unsafe_allow_html=True)
