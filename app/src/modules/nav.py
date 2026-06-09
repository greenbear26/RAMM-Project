# Idea borrowed from https://github.com/fsmosca/sample-streamlit-authenticator

# This file has functions to add links to the left sidebar based on the user's role.

import streamlit as st


# General 

def home_nav():
    st.sidebar.page_link("Home.py", label="Home", icon="🏠")


def about_page_nav():
    st.sidebar.page_link("pages/30_About.py", label="About", icon="🧠")


# Role: Citizen

def pol_strat_home_nav():
    st.sidebar.page_link(
        "pages/00_Citizen_Home.py", label="Citizen Home", icon="🏠"
    )


def world_bank_viz_nav():
    st.sidebar.page_link(
        "pages/01_Shaping_EU.py", label="Shaping EU Policies", icon="🇪🇺"
    )


def map_demo_nav():
    st.sidebar.page_link("pages/02_Explore.py", label="Explore Page", icon="🔎️")


# Role: Poly-Sci Researcher

def usaid_worker_home_nav():
    st.sidebar.page_link(
        "pages/10_Polysci_Home.py", label="Researcher Home", icon="🏠"
    )


def ngo_directory_nav():
    st.sidebar.page_link("pages/14_Org_Directory.py", label="Organization Comparison", icon="📊")


def add_ngo_nav():
    st.sidebar.page_link("pages/15_Add_Org.py", label="Add New Organization", icon="➕")


def prediction_nav():
    st.sidebar.page_link(
        "pages/11_Prediction.py", label="Meeting Prediction", icon="📈"
    )


def api_test_nav():
    st.sidebar.page_link("pages/12_API_Test.py", label="Test the API", icon="🛜")


def classification_nav():
    st.sidebar.page_link(
        "pages/13_Classification.py", label="Classification Demo", icon="🌺"
    )


# Role: Political Journalist

def journalist_home_nav():
    st.sidebar.page_link("pages/20_Journalist_Home.py", label="Journalist Home", icon="🖥️")


def ml_model_mgmt_nav():
    st.sidebar.page_link(
        "pages/21_Party_Prediction.py", label="Party Parliament Prediction", icon="🏢"
    )

def new_ml_model_nav():
    st.sidebar.page_link(
        "pages/22_Prettier_ML.py", label="New ML Model", icon="📈"
    )

# Sidebar assembly

def SideBarLinks(show_home=False):
    """
    Renders sidebar navigation links based on the logged-in user's role.
    The role is stored in st.session_state when the user logs in on Home.py.
    """

    # Logo appears at the top of the sidebar on every page
    st.sidebar.image("assets/logo.png", width=150)

    # If no one is logged in, send them to the Home (login) page
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.switch_page("Home.py")

    if show_home:
        home_nav()

    if st.session_state["authenticated"]:

        if st.session_state["role"] == "pol_strat_advisor":
            pol_strat_home_nav()
            world_bank_viz_nav()
            map_demo_nav()

        if st.session_state["role"] == "usaid_worker":
            usaid_worker_home_nav()
            ngo_directory_nav()
            add_ngo_nav()
            prediction_nav()
            # api_test_nav()
            # classification_nav()

        if st.session_state["role"] == "administrator":
            journalist_home_nav()
            ml_model_mgmt_nav()
            # new_ml_model_nav()
            
    # About link appears at the bottom for all roles
    about_page_nav()

    if st.session_state["authenticated"]:
        if st.sidebar.button("Logout"):
            del st.session_state["role"]
            del st.session_state["authenticated"]
            st.switch_page("Home.py")
