import logging
logger = logging.getLogger(__name__)

import streamlit as st
import requests
import ast
import json
import pandas as pd
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')
SideBarLinks()

st.markdown("# Which Lobbyists Are Influencing EU Party Groups?")
st.sidebar.header("Journalist View")
st.write("Select an EP party group to see which lobbyists have interacted with them the most.")

API_BASE = "http://web-api:4000"

EP_PARTIES = [
    "ECR", "EPP", "GUE/NGL", "Greens / EFA", "RE", "S&D", "No party"
]

selected_ep_party = st.selectbox(
    "Select an EP Party:",
    options=[""] + EP_PARTIES,
)

if st.button("Search", type="primary", use_container_width=True):
    if not selected_ep_party:
        st.warning("Please select an EP party.")
    else:
        try:
            resp = requests.get(f"{API_BASE}/parties/lobby-info", params={"ep_party": selected_ep_party})
            if resp.status_code == 200:
                data = resp.json()
                if not data:
                    st.info("No lobby info found for this EP party.")
                else:
                    info = data[0]

                    lobbyists         = ast.literal_eval(info["lobbyists"])
                    meetings          = ast.literal_eval(info["meetings_per_lobbyist"])
                    total_meetings    = int(info["total_meetings"])

                    st.markdown(f"### {selected_ep_party} — {total_meetings} total meetings")
                    st.markdown("---")

                    # Store Dataframe of lobbysits and their corresponding meetings in columns
                    df = pd.DataFrame([{
                        "Lobbyist": lobbyist,
                        "Meetings": meeting
                    } for lobbyist, meeting in zip(lobbyists, meetings)]).sort_values("Meetings", ascending=False, ignore_index=True)

                    st.dataframe(df)

            else:
                st.error("Failed to fetch lobby info.")
        except requests.exceptions.ConnectionError:
            st.warning("⚠️ Backend not connected.")