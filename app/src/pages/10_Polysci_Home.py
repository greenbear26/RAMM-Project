import logging
logger = logging.getLogger(__name__)

import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

# Show appropriate sidebar links for the role of the currently logged in user
SideBarLinks()

st.title(f"Welcome Political Science Researcher, {st.session_state['first_name']}.")
st.write('### What would you like to do today?')

st.caption("Browse and compare EU lobbying organizations side by side. Filter by country, policy area, and spending to identify key players.")
if st.button('View Organization Directory',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/14_Org_Directory.py')

st.caption("Search and save lobbying organizations by country and policy area to compare later.")
if st.button('Search Organizations',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/15_Add_Org.py')

st.caption("Use the regression model to predict the number of EU institution meetings an organization is likely to have based on their profile.")
if st.button('Predict Value Based on Regression Model',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/11_Prediction.py')

