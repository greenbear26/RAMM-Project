
# Main/entry-point file for LobbyLens

import logging
logging.basicConfig(format='%(filename)s:%(lineno)s:%(levelname)s -- %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

import os
import streamlit as st
import pandas as pd
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

st.session_state['authenticated'] = False

SideBarLinks(show_home=True)

logger.info("Loading the Home page of the app")

# Load users from CSVs 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_users(filepath):
    df = pd.read_csv(filepath)
    return [f"{row['first_name']} {row['last_name']}" for _, row in df.iterrows()]

citizen_options    = load_users(os.path.join(BASE_DIR, 'Mock_data', 'Citizen_DATA.csv'))
researcher_options = load_users(os.path.join(BASE_DIR, 'Mock_data', 'PolySci_DATA.csv'))
journalist_options = load_users(os.path.join(BASE_DIR, 'Mock_data', 'Journalist_DATA.csv'))

# Page content
st.title("Welcome to LobbyLens!")
st.write("---")

# Persona 1: European Citizen
st.subheader("European Citizen:")
selected_citizen = st.selectbox("Select citizen", citizen_options,
                                key="citizen_select", label_visibility="collapsed")
if st.button("Login", key="citizen_login", type="primary"):
    st.session_state['authenticated'] = True
    st.session_state['role'] = 'pol_strat_advisor'
    st.session_state['first_name'] = selected_citizen.split()[0]
    st.session_state['last_name'] = selected_citizen.split()[1]
    logger.info(f"Logging in as Citizen: {selected_citizen}")
    st.switch_page('pages/00_Citizen_Home.py')

st.write("")
# Persona 2: Political Science Researcher
st.subheader("Political Science Researcher:")
researcher_options = ["Jacques Clouseau"]
selected_researcher = st.selectbox("Select researcher", researcher_options,
                                   key="researcher_select", label_visibility="collapsed")
if st.button("Login", key="researcher_login", type="primary"):
    st.session_state['authenticated'] = True
    st.session_state['role'] = 'usaid_worker'
    st.session_state['first_name'] = selected_researcher.split()[0]
    st.session_state['last_name'] = selected_researcher.split()[1]
    logger.info(f"Logging in as Researcher: {selected_researcher}")
    st.switch_page('pages/10_Polysci_Home.py')

st.write("")

# Political Party Journalist 
st.subheader("Political Party Journalist:")
journalist_options = ["Tintin"]
selected_journalist = st.selectbox("Select journalist", journalist_options,
                                   key="journalist_select", label_visibility="collapsed")
if st.button("Login", key="journalist_login", type="primary"):
    st.session_state['authenticated'] = True
    st.session_state['role'] = 'administrator'
    st.session_state['first_name'] = selected_journalist.split()[0]
    st.session_state['last_name'] = selected_journalist.split()[1]
    logger.info(f"Logging in as Journalist: {selected_journalist}")
    st.switch_page('pages/20_Journalist_Home.py')