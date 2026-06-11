import logging
logger = logging.getLogger(__name__)

import streamlit as st
import pandas as pd
import requests
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')
SideBarLinks()

st.markdown("# What Are EU Parties Fighting For?")
st.write("Pick a country and EP party to see which parties are active and what they stand for.")

API_BASE = "http://web-api:4000"

if "selected_countries" not in st.session_state:
    st.session_state.selected_countries = []
if "selected_ep_parties" not in st.session_state:
    st.session_state.selected_ep_parties = []

st.cache_data.clear()

COUNTRIES = [
    "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus",
    "Czech Republic", "Denmark", "Estonia", "Finland", "France",
    "Germany", "Greece", "Hungary", "Ireland", "Italy", "Latvia",
    "Lithuania", "Luxembourg", "Netherlands", "Poland",
    "Portugal", "Romania", "Slovakia", "Slovenia", "Spain", "Sweden",
]

EP_PARTIES = [
    "ECR", "EPP", "GUE/NGL", "Greens / EFA", "RE", "S&D", "No party"
]

st.markdown("### Pick a Country")
valid_country_defaults = [c for c in st.session_state.selected_countries if c in COUNTRIES]
selected_countries = st.multiselect(
    "Select one or more countries:",
    options=COUNTRIES,
    default=valid_country_defaults,
)
st.session_state.selected_countries = selected_countries

st.markdown("---")

st.markdown("### Pick an EP Party")
valid_ep_defaults = [e for e in st.session_state.selected_ep_parties if e in EP_PARTIES]
selected_ep_parties = st.multiselect(
    "Select one or more EP parties:",
    options=EP_PARTIES,
    default=valid_ep_defaults,
)
st.session_state.selected_ep_parties = selected_ep_parties

st.markdown("---")



def fetch_parties(countries, ep_parties):
    country_list  = countries  if countries  else [None]
    ep_party_list = ep_parties if ep_parties else [None]

    seen = {}
    for c in country_list:
        for e in ep_party_list:
            params = {"limit": 200}
            if c: params["country"]  = c
            if e: params["ep_party"] = e
            try:
                resp = requests.get(f"{API_BASE}/parties", params=params)
                if resp.status_code == 200:
                    for party in resp.json():
                        seen[party["party_id"]] = party
            except requests.exceptions.ConnectionError:
                st.warning("⚠️ Backend not connected.")
                return []
    return sorted(seen.values(), key=lambda p: p.get("left_right") or 0, reverse=True)


def fetch_lobby_info(ep_parties):
    seen = {}
    ep_party_list = ep_parties if ep_parties else [None]
    for e in ep_party_list:
        params = {}
        if e: params["ep_party"] = e
        try:
            resp = requests.get(f"{API_BASE}/parties/lobby-info", params=params)
            if resp.status_code == 200:
                for info in resp.json():
                    seen[info["ep_party"]] = info
        except requests.exceptions.ConnectionError:
            st.warning("⚠️ Backend not connected.")
            return []
    return sorted(seen.values(), key=lambda i: i.get("total_meetings") or 0, reverse=True)


if st.button("Search", type="primary", use_container_width=True):
    if not selected_countries and not selected_ep_parties:
        st.warning("Please select at least one country or EP party.")
    else:
        results = fetch_parties(selected_countries, selected_ep_parties)

        st.markdown(f"### Results: {len(results)} parties found")

        if not results:
            st.info("No parties found. Try different filters.")
        else:
            table = [{
                "Party Name":    p.get("party_name_english"),
                "Country":       p.get("country_name"),
                "EP Party":      p.get("ep_party"),
                "Family":        p.get("family_name"),
                "Left/Right":    p.get("left_right"),
                "Populist":      bool(p.get("populist")),
                "Far Right":     bool(p.get("farright")),
                "Far Left":      bool(p.get("farleft")),
                "Eurosceptic":   bool(p.get("eurosceptic")),
                "In Parliament": bool(p.get("in_parliament")),
            } for p in results]

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
                label="⬇ Download parties as CSV",
                data=df_all.to_csv(index=False),
                file_name="eu_parties.csv",
                mime="text/csv",
            )
        st.markdown("---")
        st.markdown("### Lobby Activity by EP Party")

        lobby_results = fetch_lobby_info(selected_ep_parties)

        if not lobby_results:
            st.info("No lobby info found for selected EP parties.")
        else:
            lobby_table = [{
                "EP Party":       i.get("ep_party"),
                "Total Meetings": i.get("total_meetings"),
            } for i in lobby_results]
            st.dataframe(lobby_table, use_container_width=True)
            df_lobby = pd.DataFrame(lobby_table)
            st.download_button(
                label="⬇ Download lobby activity as CSV",
                data=df_lobby.to_csv(index=False),
                file_name="lobby_activity.csv",
                mime="text/csv",
            )