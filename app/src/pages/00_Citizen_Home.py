import logging
logger = logging.getLogger(__name__)

import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

# Show appropriate sidebar links for the role of the currently logged in user
SideBarLinks()

st.title(f"Welcome Citizen, {st.session_state['first_name']}.")
st.write('### What would you like to do today?')

if st.button('View Shaping EU Policies',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/01_Shaping_EU.py')

if st.button('View Explore Page',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/02_Explore.py')
