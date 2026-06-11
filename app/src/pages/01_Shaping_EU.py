import logging
logger = logging.getLogger(__name__)

import streamlit as st
import pandas as pd
import requests
import pandas as pd
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')
SideBarLinks()

st.markdown("# Who is Shaping EU Policies?")

st.markdown("""
This page lets you filter those organizations by **policy area** and **country of origin**
so you can see exactly who is trying to shape the rules that affect your life.

Select one or more policy areas and countries below, then hit **Search** to surface matching
organizations ranked by lobbying spend. You can also **download** the results as a CSV
to explore the data further.
""")

API_BASE = "http://web-api:4000"

if "selected_policies" not in st.session_state:
    st.session_state.selected_policies = []
if "selected_countries" not in st.session_state:
    st.session_state.selected_countries = []

st.cache_data.clear()
POLICIES = ["Artificial Intelligence","Climate & Energy","Healthcare","Defence & Security","Finance & Banking","Agriculture","Digital Markets","Transport"]

COUNTRIES = [
    "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus",
    "Czech Republic", "Denmark", "Estonia", "Finland", "France",
    "Germany", "Greece", "Hungary", "Ireland", "Italy", "Latvia",
    "Lithuania", "Luxembourg", "Malta", "Netherlands", "Poland",
    "Portugal", "Romania", "Slovakia", "Slovenia", "Spain", "Sweden",
]

st.markdown("### Pick Policies")
valid_policy_defaults = [p for p in st.session_state.selected_policies if p in POLICIES]
selected_policies = st.multiselect(
    "Select one or more policy areas:",
    options=POLICIES,
    default=valid_policy_defaults,
)
st.session_state.selected_policies = selected_policies

st.markdown("---")

st.markdown("### Pick a Country")
valid_country_defaults = [c for c in st.session_state.selected_countries if c in COUNTRIES]
selected_countries = st.multiselect(
    "Select one or more countries:",
    options=COUNTRIES,
    default=valid_country_defaults,
)
st.session_state.selected_countries = selected_countries

st.markdown("---")



def fetch_orgs(policies, countries):
    policy_list  = policies  if policies  else [None]
    country_list = countries if countries else [None]

    seen = {}
    for p in policy_list:
        for c in country_list:
            params = {"limit": 200}
            if p: params["policy_area"] = p
            if c: params["country"]     = c
            try:
                resp = requests.get(f"{API_BASE}/organizations", params=params)
                if resp.status_code == 200:
                    for org in resp.json():
                        seen[org["org_id"]] = org
            except requests.exceptions.ConnectionError:
                st.warning("⚠️ Backend not connected.")
                return []
    return sorted(seen.values(), key=lambda o: o.get("lobbying_cost") or 0, reverse=True)


if "org_results_table" not in st.session_state:
    st.session_state.org_results_table = []

if st.button("Search", type="primary", use_container_width=True):
    if not selected_policies and not selected_countries:
        st.warning("Please select at least one policy or country.")
    else:
        results = fetch_orgs(selected_policies, selected_countries)
        table = []
        if results:
            table = [{
                "Name":                 o.get("name"),
                "Policy areas":         o.get("policy_areas").strip("[]").replace('"', '') if o.get("policy_areas") else "",
                "Lobbying cost":        o.get("lobbying_cost"),
                "Interest represented": o.get("interest_represented"),
                "Country":              o.get("country_name"),
            } for o in results]

            df_all = pd.DataFrame(table)

            countries_in_results = df_all["Country"].dropna().unique().tolist()
            if len(countries_in_results) > 1:
                tabs = st.tabs(countries_in_results)
                for tab, country in zip(tabs, countries_in_results):
                    with tab:
                        df_country = df_all[df_all["Country"] == country].drop(columns=["Country"])
                        st.dataframe(df_country, use_container_width=True, hide_index=True)
            else:
                st.dataframe(table, use_container_width=True, hide_index=True)

            st.download_button(
                label="⬇ Download organizations as CSV",
                data=df_all.to_csv(index=False),
                file_name="eu_organizations.csv",
                mime="text/csv",
            )
