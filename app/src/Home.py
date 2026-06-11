import logging
logging.basicConfig(format='%(filename)s:%(lineno)s:%(levelname)s -- %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

import os
import streamlit as st
import pandas as pd
from PIL import Image
from modules.nav import SideBarLinks

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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_users(filepath):
    df = pd.read_csv(filepath)
    return [f"{row['first_name']} {row['last_name']}" for _, row in df.iterrows()]

citizen_options    = sorted(load_users(os.path.join(BASE_DIR, 'Mock_data', 'Citizen_DATA.csv')),    key=lambda name: name.split()[-1])
researcher_options = sorted(load_users(os.path.join(BASE_DIR, 'Mock_data', 'PolySci_DATA.csv')),    key=lambda name: name.split()[-1])
journalist_options = sorted(load_users(os.path.join(BASE_DIR, 'Mock_data', 'Journalist_DATA.csv')), key=lambda name: name.split()[-1])
# Hero section
st.markdown("""
<div style="
    background: linear-gradient(135deg, #0F172A 0%, #1E3A5F 60%, #1a4a7a 100%);
    border-radius: 14px;
    padding: 32px 40px;
    margin-bottom: 28px;
    text-align: center;
">
    <h1 style="color: #FFFFFF; font-size: 38px; font-weight: 800; margin: 0 0 8px 0;
               letter-spacing: -1px;">LobbyLens</h1>
    <p style="color: #93C5FD; font-size: 16px; margin: 0 0 10px 0; font-weight: 500;">
        Transparency into EU Lobbying &amp; Political Influence
    </p>
    <p style="color: #CBD5E1; font-size: 13px; max-width: 540px; margin: 0 auto; line-height: 1.6;">
        Explore how organizations shape European Union policy. Track lobbying spend,
        compare organizational influence, and uncover the forces behind EU decision-making.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<p style="text-align:center; color:#64748B; font-size:12px; letter-spacing:2px;
   text-transform:uppercase; font-weight:600; margin-bottom:16px;">
   Select your role to continue
</p>
""", unsafe_allow_html=True)


# Card style
CARD_STYLE = """
background: #1E293B;
border: 1px solid #334155;
border-radius: 10px;
padding: 14px 16px;
margin-bottom: 10px;
height: 150px;
border-radius: 12px;
padding: 18px 18px 14px 18px;
margin-bottom: 10px;
height: 160px;
overflow: hidden;
"""

c1, c2, c3 = st.columns(3)

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f'<div style="{CARD_STYLE}"><h3 style="color:#FFFFFF; margin:0 0 4px 0; font-size:15px; font-weight:700;">European Citizen</h3><p style="color:#94A3B8; font-size:11px; line-height:1.5; margin:0;">Explore who funds EU lobbying and which policy areas are most contested.</p></div>', unsafe_allow_html=True)
    selected_citizen = st.selectbox("Select citizen", citizen_options, key="citizen_select", label_visibility="collapsed")
    st.markdown(f'<div style="{CARD_STYLE}"><h3 style="color:#FFFFFF; margin:0 0 6px 0; font-size:16px; font-weight:700;">European Citizen</h3><p style="color:#94A3B8; font-size:12px; line-height:1.6; margin:0;">Explore which organizations are shaping EU policy in your country. Understand who funds political lobbying and which policy areas are most contested.</p></div>', unsafe_allow_html=True)
    selected_citizen = st.selectbox("Select citizen", citizen_options, key="citizen_select", label_visibility="collapsed")
    if st.button("Login as Citizen", key="citizen_login", type="primary", use_container_width=True):
        st.session_state['authenticated'] = True
        st.session_state['role'] = 'pol_strat_advisor'
        st.session_state['first_name'] = selected_citizen.split()[0]
        st.session_state['last_name'] = selected_citizen.split()[1]
        logger.info(f"Logging in as Citizen: {selected_citizen}")
        st.switch_page('pages/00_Citizen_Home.py')

with c2:
    st.markdown(f'<div style="{CARD_STYLE}"><h3 style="color:#FFFFFF; margin:0 0 4px 0; font-size:15px; font-weight:700;">Political Science Researcher</h3><p style="color:#94A3B8; font-size:11px; line-height:1.5; margin:0;">Compare lobbying organizations, run ML predictions, and analyse spending patterns.</p></div>', unsafe_allow_html=True)
    selected_researcher = st.selectbox("Select researcher", researcher_options, key="researcher_select", label_visibility="collapsed")
    st.markdown(f'<div style="{CARD_STYLE}"><h3 style="color:#FFFFFF; margin:0 0 6px 0; font-size:16px; font-weight:700;">Political Science Researcher</h3><p style="color:#94A3B8; font-size:12px; line-height:1.6; margin:0;">Compare lobbying organizations side by side, run ML influence predictions, and analyse spending patterns across policy areas and EU institutions.</p></div>', unsafe_allow_html=True)
    selected_researcher = st.selectbox("Select researcher", researcher_options, key="researcher_select", label_visibility="collapsed")
    if st.button("Login as Researcher", key="researcher_login", type="primary", use_container_width=True):
        st.session_state['authenticated'] = True
        st.session_state['role'] = 'usaid_worker'
        st.session_state['first_name'] = selected_researcher.split()[0]
        st.session_state['last_name'] = selected_researcher.split()[1]
        logger.info(f"Logging in as Researcher: {selected_researcher}")
        st.switch_page('pages/10_Polysci_Home.py')

with c3:
    st.markdown(f'<div style="{CARD_STYLE}"><h3 style="color:#FFFFFF; margin:0 0 4px 0; font-size:15px; font-weight:700;">Political Party Journalist</h3><p style="color:#94A3B8; font-size:11px; line-height:1.5; margin:0;">Profile EU parties, predict parliament outcomes, and track populist movements.</p></div>', unsafe_allow_html=True)
    selected_journalist = st.selectbox("Select journalist", journalist_options, key="journalist_select", label_visibility="collapsed")
    st.markdown(f'<div style="{CARD_STYLE}"><h3 style="color:#FFFFFF; margin:0 0 6px 0; font-size:16px; font-weight:700;">Political Party Journalist</h3><p style="color:#94A3B8; font-size:12px; line-height:1.6; margin:0;">Predict parliament seat outcomes, profile political parties across EU member states, and track how populist and far-right movements influence EU policy.</p></div>', unsafe_allow_html=True)
    selected_journalist = st.selectbox("Select journalist", journalist_options, key="journalist_select", label_visibility="collapsed")
    if st.button("Login as Journalist", key="journalist_login", type="primary", use_container_width=True):
        st.session_state['authenticated'] = True
        st.session_state['role'] = 'administrator'
        st.session_state['first_name'] = selected_journalist.split()[0]
        st.session_state['last_name'] = selected_journalist.split()[1]
        logger.info(f"Logging in as Journalist: {selected_journalist}")
        st.switch_page('pages/20_Journalist_Home.py')

st.markdown("""
<div style="margin-top: 32px; text-align: center; color: #94A3B8; font-size: 11px;">
<div style="margin-top: 32px; text-align: center; color: #94A3B8; font-size: 11px;">
    LobbyLens &nbsp;·&nbsp; EU Lobbying Transparency Platform &nbsp;·&nbsp;
    Data sourced from the EU Transparency Register &amp; LobbyFacts
</div>
""", unsafe_allow_html=True)