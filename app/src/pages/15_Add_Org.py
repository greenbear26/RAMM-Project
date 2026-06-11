import logging
logger = logging.getLogger(__name__)

import streamlit as st
import requests
from modules.nav import SideBarLinks

st.set_page_config(page_title="Add Organization", page_icon="📊", layout='wide')

SideBarLinks()

st.markdown("# Add Organization")

st.markdown("""
Filter lobbying organizations by **policy area** and **country**, then hit **Search** to browse
results ranked by lobbying spend. Hit **Save** on any organization to add it to your saved list,
then head to the **Organization Comparison** page to compare two organizations head to head.
""")

if "saved_orgs" not in st.session_state:
    st.session_state.saved_orgs = []

POLICY_AREAS = [
    "All",
    "Agriculture",
    "Artificial Intelligence",
    "Climate & Energy",
    "Defence & Security",
    "Digital Markets",
    "Finance & Banking",
    "Healthcare",
    "Other",
    "Transport",
]

COUNTRIES = [
    "All",
    "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus",
    "Czech Republic", "Denmark", "Estonia", "Finland", "France",
    "Germany", "Greece", "Hungary", "Ireland", "Italy",
    "Latvia", "Lithuania", "Luxembourg", "Malta", "Netherlands",
    "Poland", "Portugal", "Romania", "Slovenia", "Spain", "Sweden",
]

st.divider()
st.markdown("### Search for an organization")

filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    selected_policy = st.selectbox("Filter by Policy Area", POLICY_AREAS)
with filter_col2:
    selected_country = st.selectbox("Filter by Country", COUNTRIES)

search_btn = st.button("Search", use_container_width=False)

if search_btn or "org_results" not in st.session_state:
    try:
        params = {}
        if selected_policy != "All":
            params["policy_area"] = selected_policy
        if selected_country != "All":
            params["country"] = selected_country

        resp = requests.get("http://web-api:4000/organizations", params=params)
        if resp.status_code == 200:
            st.session_state.org_results = resp.json()
            st.session_state.last_policy = selected_policy
            st.session_state.last_country = selected_country
        else:
            st.session_state.org_results = []
    except Exception:
        st.warning("Backend not connected.")
        st.session_state.org_results = []

if (st.session_state.get("last_policy") != selected_policy or
        st.session_state.get("last_country") != selected_country):
    try:
        params = {}
        if selected_policy != "All":
            params["policy_area"] = selected_policy
        if selected_country != "All":
            params["country"] = selected_country

        resp = requests.get("http://web-api:4000/organizations", params=params)
        if resp.status_code == 200:
            st.session_state.org_results = resp.json()
        else:
            st.session_state.org_results = []
    except Exception:
        st.session_state.org_results = []
    st.session_state.last_policy = selected_policy
    st.session_state.last_country = selected_country

results = st.session_state.get("org_results", [])
st.divider()

tab_results, tab_saved = st.tabs([
    f"Results ({len(results)})",
    f"Saved ({len(st.session_state.saved_orgs)})",
])

with tab_results:
    if results:
        saved_names = {o.get("name") for o in st.session_state.saved_orgs}
        scroll = st.container(height=520, border=False)
        with scroll:
            for org in results:
                already = org.get("name") in saved_names
                r1, r2, r3 = st.columns([4, 2, 1])
                with r1:
                    st.markdown(f"**{org['name']}**")
                    st.caption(f"{org.get('country_name', '—')} · €{org.get('lobbying_cost', 0):,.0f}")
                with r2:
                    st.markdown(f"{org.get('interest_represented', '—')}")
                with r3:
                    if already:
                        st.caption("Saved")
                    else:
                        if st.button("Save", key=f"save_{org['org_id']}"):
                            st.session_state.saved_orgs.append(org)
                            st.rerun()
                st.divider()
    else:
        st.info("No organizations found. Try adjusting the filters.")

with tab_saved:
    if not st.session_state.saved_orgs:
        st.info("No saved organizations yet. Search and save organizations from the Results tab.")
    else:
        scroll_saved = st.container(height=520, border=False)
        with scroll_saved:
            for i, org in enumerate(st.session_state.saved_orgs):
                s1, s2, s3 = st.columns([4, 2, 1])
                with s1:
                    st.markdown(f"**{org.get('name', '—')}**")
                    st.caption(f"{org.get('country_name', '—')} · €{org.get('lobbying_cost', 0):,.0f}")
                with s2:
                    st.markdown(f"{org.get('interest_represented', '—')}")
                with s3:
                    if st.button("Remove", key=f"remove_{i}"):
                        st.session_state.saved_orgs.pop(i)
                        st.rerun()
                st.divider()
