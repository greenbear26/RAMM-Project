import logging
logger = logging.getLogger(__name__)

import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

SideBarLinks()

st.title(f"Welcome Political Party Journalist, {st.session_state['first_name']}.")
st.write('### What would you like to do today?')

if st.button('Predict party parliament probability',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/21_Party_Prediction.py')