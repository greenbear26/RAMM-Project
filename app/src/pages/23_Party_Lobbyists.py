import logging
logger = logging.getLogger(__name__)

import streamlit as st
import requests
import ast
import pandas as pd
import plotly.express as px
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')
SideBarLinks()

st.markdown("# Which Lobbyists Are Influencing EU Party Groups?")
st.write("Select an European Parliament party to see which lobbyists have interacted with them the most.")

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

                    lobbyists      = ast.literal_eval(info["lobbyists"])
                    meetings       = ast.literal_eval(info["meetings_per_lobbyist"])
                    total_meetings = int(info["total_meetings"])

                    st.markdown(f"### {selected_ep_party} — {total_meetings} total meetings")
                    st.markdown("---")

                    df = pd.DataFrame([{
                        "Lobbyist": lobbyist,
                        "Meetings": meeting
                    } for lobbyist, meeting in zip(lobbyists, meetings)]).sort_values("Meetings", ascending=False, ignore_index=True)

                    st.markdown("#### Top 20 Lobbyists by Meeting Count")
                    fig = px.bar(
                        df.head(20),
                        x="Meetings",
                        y="Lobbyist",
                        orientation="h",
                    )
                    fig.update_layout(
                        yaxis=dict(autorange="reversed"),
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="sans-serif", size=13),
                        margin=dict(l=20, r=20, t=20, b=20),
                        xaxis=dict(showgrid=True, gridcolor="#251876"),
                        yaxis_title="",
                        xaxis_title="Number of Meetings",
                    )
                    fig.update_traces(marker_color="#b08850")
                    st.plotly_chart(fig, use_container_width=True)

                    st.markdown("---")
                    with st.expander("View full table"):
                        st.dataframe(df, use_container_width=True, hide_index=True)

                    st.download_button(
                        label="⬇ Download as CSV",
                        data=df.to_csv(index=False),
                        file_name=f"{selected_ep_party}_lobbyists.csv",
                        mime="text/csv",
                    )
            else:
                st.error("Failed to fetch lobby info.")
        except requests.exceptions.ConnectionError:
            st.warning("⚠️ Backend not connected.")