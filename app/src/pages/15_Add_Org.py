import logging
logger = logging.getLogger(__name__)

import streamlit as st
import requests
from modules.nav import SideBarLinks

st.set_page_config(page_title="Add New NGO", page_icon="➕", layout='wide')

SideBarLinks()

st.markdown("# Add Organization")
st.sidebar.header("Add New NGO")
st.write("Search for existing organizations to save to your comparison list, or create a brand new one.")

API_BASE = "http://web-api:4000"

# Fallback dropdown options (used if backend fetch fails)
POLICY_AREAS_FALLBACK = [
    "", "Artificial Intelligence", "Climate & Energy", "Healthcare",
    "Defence & Security", "Finance & Banking", "Agriculture",
    "Digital Markets", "Transport",
]

COUNTRIES = [
    "", "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czech Republic",
    "Denmark", "Estonia", "Finland", "France", "Germany", "Greece", "Hungary",
    "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg", "Malta", "Netherlands",
    "Poland", "Portugal", "Romania", "Slovakia", "Slovenia", "Spain", "Sweden"
]


# Load policy areas live from the backend so they always match the DB
@st.cache_data(ttl=300)
def fetch_policy_areas():
    try:
        resp = requests.get(f"{API_BASE}/policy-areas")
        if resp.status_code == 200:
            names = [pa["name"] for pa in resp.json()]
            return [""] + sorted(names)
    except Exception:
        pass
    return POLICY_AREAS_FALLBACK

POLICY_AREAS = fetch_policy_areas()

# Session state
if "saved_orgs" not in st.session_state:
    st.session_state.saved_orgs = []
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "searched" not in st.session_state:
    st.session_state.searched = False

# Tabs
tab_search, tab_create = st.tabs(["🔍 Search & Save", "➕ Create New"])


# TAB 1 — Search & Save
with tab_search:
    st.markdown("### Find an Organization")
    st.write("Search by policy area or country and save results to your comparison list.")

    f1, f2 = st.columns(2)
    with f1:
        policy_filter = st.selectbox("Policy Area", options=POLICY_AREAS, key="policy_search")
    with f2:
        country_filter = st.selectbox("Country", options=COUNTRIES, key="country_search")

    if st.button("Search 🔍", type="primary", use_container_width=True):
        params = {}
        if policy_filter:  params["policy_area"] = policy_filter
        if country_filter: params["country"]     = country_filter
        try:
            resp = requests.get(f"{API_BASE}/organizations", params=params)
            st.session_state.search_results = resp.json() if resp.status_code == 200 else []
            st.session_state.searched = True
        except requests.exceptions.ConnectionError:
            st.session_state.search_results = []
            st.warning("⚠️ Backend not connected yet.")

    if st.session_state.search_results:
        st.markdown(f"**{len(st.session_state.search_results)} results found**")
        st.markdown("---")
        for org in st.session_state.search_results[:10]:
            already = org["org_id"] in [o["org_id"] for o in st.session_state.saved_orgs]
            r1, r2, r3 = st.columns([4, 2, 1])
            with r1:
                st.markdown(f"**{org['name']}**")
                st.caption(f"{org.get('country_code','—')} · {org.get('interest_represented','—')}")
            with r2:
                st.markdown(f"€{org.get('lobbying_cost', 0):,.0f}")
            with r3:
                if already:
                    st.caption("✅ Saved")
                else:
                    if st.button("Save", key=f"save_{org['org_id']}", use_container_width=True):
                        st.session_state.saved_orgs.append(org)
                        st.rerun()
    elif st.session_state.searched:
        st.info("No results found. Try different filters.")

    if st.session_state.saved_orgs:
        st.markdown("---")
        st.markdown(f"**{len(st.session_state.saved_orgs)} org(s) saved to your comparison list.** "
                    f"Go to the **Organization Comparison** page to compare them.")


# TAB 2 — Create New
with tab_create:
    st.markdown("### Create a New Organization")
    st.write("Fill in the fields below to add a new organization to the database.")

    with st.form("create_org_form"):
        c1, c2 = st.columns(2)
        with c1:
            name          = st.text_input("Organization Name *")
            country       = st.selectbox("Country *", options=COUNTRIES, key="country_create")
            lobbying_cost = st.number_input("Lobbying Cost (€)", min_value=0.0, step=1000.0)
        with c2:
            interest_represented = st.selectbox("Policy Area *", options=POLICY_AREAS, key="policy_create")
            members_fte          = st.number_input("FTE Members", min_value=0, step=1)
            lobbyfacts_url       = st.text_input("LobbyFacts URL", placeholder="https://...")

        submitted = st.form_submit_button("Create Organization", type="primary", use_container_width=True)

    if submitted:
        if not name or not country or not interest_represented:
            st.error("Please fill in all required fields (marked with *).")
        else:
            payload = {
                "name":                 name,
                "country_code":         country,
                "lobbying_cost":        lobbying_cost,
                "members_fte":          int(members_fte),
                "interest_represented": interest_represented,
            }
            try:
                resp = requests.post(f"{API_BASE}/organizations", json=payload)
                if resp.status_code == 201:
                    new_id = resp.json().get("org_id")
                    st.success(f"✅ Organization **{name}** created successfully! (ID: {new_id})")
                    payload["org_id"] = new_id
                    st.session_state.saved_orgs.append(payload)
                else:
                    st.error(f"Failed to create organization. Server response: {resp.status_code}")
            except requests.exceptions.ConnectionError:
                st.warning("⚠️ Backend not connected yet.")