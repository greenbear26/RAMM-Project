import logging
logger = logging.getLogger(__name__)

import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

# Show appropriate sidebar links for the role of the currently logged in user
SideBarLinks()

st.title(f"Welcome Political Science Researcher, {st.session_state['first_name']}.")
st.write('### What would you like to do today?')

if st.button('View NGO Directory',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/14_NGO_Directory.py')

if st.button('Add New NGO',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/15_Add_Org.py')

if st.button('Predict Value Based on Regression Model',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/11_Prediction.py')
