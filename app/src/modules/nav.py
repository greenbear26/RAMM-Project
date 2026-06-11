# Idea borrowed from https://github.com/fsmosca/sample-streamlit-authenticator

# This file has functions to add links to the left sidebar based on the user's role.

import streamlit as st


# General 

def home_nav():
    st.sidebar.page_link("Home.py", label="Home", icon="🏠")


def about_page_nav():
    st.sidebar.page_link("pages/30_About.py", label="About", icon="🧠")


# Role: Citizen

def citizen_home_nav():
    st.sidebar.page_link(
        "pages/00_Citizen_Home.py", label="Citizen Home", icon="🏠"
    )


def shaping_eu_nav():
    st.sidebar.page_link(
        "pages/01_Shaping_EU.py", label="Shaping EU Policies", icon="🇪🇺"
    )


def explore_organization_nav():
    st.sidebar.page_link("pages/02_Explore_Lobbying_Facts.py", label="Explore Facts", icon="🔎️")


# Role: Poly-Sci Researcher

def researcher_home_nav():
    st.sidebar.page_link(
        "pages/10_Polysci_Home.py", label="Researcher Home", icon="🏠"
    )

def lobby_prediction_nav():
    st.sidebar.page_link(
        "pages/11_Prediction.py", label="ML Influence Prediction", icon="🤖"
    )

def search_organization_nav():
    st.sidebar.page_link("pages/12_Search_Org.py", label="Search Organizations", icon="🔍")

def compare_organization_nav():
    st.sidebar.page_link("pages/13_Org_Compare.py", label="Organization Comparison", icon="📊")


# Role: Political Journalist

def journalist_home_nav():
    st.sidebar.page_link("pages/20_Journalist_Home.py", label="Journalist Home", icon="🖥️")

def party_parliament_prediction_nav():
    st.sidebar.page_link(
        "pages/22_Party_Prediction.py", label="Party Parliament Prediction", icon="🏢"
    )

def party_explore_nav():
    st.sidebar.page_link(
        "pages/21_Party_Learnings.py", label="Explore Parties", icon="🎉"
    )

def party_lobbyists_nav():
    st.sidebar.page_link(
        "pages/23_Party_Lobbyists.py", label="Party Lobbyists", icon="⚖️"
    )
# Sidebar assembly

def SideBarLinks(show_home=True):
    """
    Renders sidebar navigation links based on the logged-in user's role.
    The role is stored in st.session_state when the user logs in on Home.py.
    """

    # Logo appears at the top of the sidebar on every page
    st.sidebar.image("assets/Lobby_logo.png", use_container_width=True)

    # If no one is logged in, send them to the Home (login) page
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.switch_page("Home.py")

    if show_home:
        home_nav()

    if st.session_state["authenticated"]:

        if st.session_state["role"] == "citizen":
            citizen_home_nav()
            shaping_eu_nav()
            explore_organization_nav()

        if st.session_state["role"] == "researcher":
            researcher_home_nav()
            lobby_prediction_nav()
            search_organization_nav()
            compare_organization_nav()

        if st.session_state["role"] == "journalist":
            journalist_home_nav()
            party_explore_nav()
            party_parliament_prediction_nav()
            party_lobbyists_nav()
            
    # About link appears at the bottom for all roles
    about_page_nav()

    if st.session_state["authenticated"]:
        if st.sidebar.button("Logout"):
            del st.session_state["role"]
            del st.session_state["authenticated"]
            st.switch_page("Home.py")
