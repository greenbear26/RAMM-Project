import logging
logger = logging.getLogger(__name__)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import os

st.set_page_config(page_title="Meeting Prediction", layout="wide")

from modules.nav import SideBarLinks
SideBarLinks()

st.markdown("# Meeting Prediction")

st.markdown("""
Enter an organization's lobbying spend, number of staff, and EP access passes to get an
ML-predicted estimate of how many European Parliament meetings it is likely to secure.
Use the scatter plot to see how the prediction compares against real organizations in the dataset.
""")

# Load lobbyfacts data for scatter plot
@st.cache_data
def load_lobbyfacts():
    paths = [
        os.path.join(os.path.dirname(__file__), '..', 'lobbyfacts_with_p.csv'),
        os.path.join(os.path.dirname(__file__), '..', 'datasets', 'lobbying', 'lobbyfacts_merged.csv'),
    ]
    for p in paths:
        if os.path.exists(p):
            return pd.read_csv(p)
    return None

df_lobbyfacts = load_lobbyfacts()

# Session state
if "saved_comparisons" not in st.session_state:
    st.session_state.saved_comparisons = []
if "prediction_result" not in st.session_state:
    st.session_state.prediction_result = None
if "prediction_inputs" not in st.session_state:
    st.session_state.prediction_inputs = None

country_options = [
    "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czech Republic",
    "Denmark", "Estonia", "Finland", "France", "Germany", "Greece", "Hungary",
    "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg", "Malta", "Netherlands",
    "Poland", "Portugal", "Romania", "Slovenia", "Spain", "Sweden",
]

interest_options = [
    "Advances interests of their clients",
    "Does not represent commercial interests",
    "Promotes their own interests or the collective interests of their members",
]

with st.form("lobby_prediction_form"):
    col1, col2 = st.columns(2)

    with col1:
        lobbying_cost = st.number_input(
            "Lobbying cost (€)",
            min_value=0.0, step=1000.0, value=10000.0,
            help="Total annual budget the organization spends on EU lobbying activities, including staff, events, and external consultants.",
        )
        ep_passes = st.number_input(
            "EP passes",
            min_value=0.0, step=1.0, value=10.0,
            help="European Parliament access passes held by the organization. These badges allow staff to enter EP buildings and directly engage with MEPs and their offices.",
        )
        members_fte = st.number_input(
            "Members / FTE",
            min_value=0.0, step=1.0, value=25.0,
            help="Full-time equivalent (FTE) staff or members dedicated to lobbying. For trade associations this is the number of member organizations; for companies it is the number of in-house lobbyists.",
        )

    with col2:
        country = st.selectbox(
            "Country",
            country_options,
            help="The EU member state where the organization is headquartered. Proximity to Brussels and national political weight can affect access to EU institutions.",
        )
        interest = st.selectbox(
            "Interest representation",
            interest_options,
            help="How the organization describes its lobbying purpose: acting for clients (consultancies), representing its own/members' interests (trade bodies, companies), or a non-commercial mission (NGOs, think-tanks).",
        )

    submitted = st.form_submit_button("Predict")

if submitted:
    payload = {
        "lobbying_cost": lobbying_cost,
        "ep_passes": ep_passes,
        "members_fte": members_fte,
        "country": country,
        "interest": interest,
    }

    api_urls = [
        "http://web-api:4000/lobby/prediction",
        "http://localhost:4000/lobby/prediction",
    ]

    response = None
    last_error = None
    for api_url in api_urls:
        try:
            response = requests.post(api_url, json=payload, timeout=10)
            if response.ok:
                break
            try:
                last_error = response.json().get("error", response.text)
            except ValueError:
                last_error = response.text
        except requests.exceptions.RequestException as exc:
            last_error = str(exc)

    if response is None:
        st.error(f"Could not reach the prediction service: {last_error}")
    elif not response.ok:
        st.error(f"Prediction request failed: {last_error}")
    else:
        result = response.json()
        # Store result in session state so it persists after Save button clicks
        st.session_state.prediction_result = result["prediction"]
        st.session_state.prediction_inputs = {
            "lobbying_cost": lobbying_cost,
            "ep_passes": ep_passes,
            "members_fte": members_fte,
            "country": country,
            "interest": interest,
        }

# Show results if we have a prediction stored
if st.session_state.prediction_result is not None:
    prediction = st.session_state.prediction_result
    inputs = st.session_state.prediction_inputs

    st.divider()
    st.subheader("Prediction Result")
               
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Predicted EP Meetings", f"{prediction:.1f}")
    with c2:
        st.metric("Lobbying Cost", f"€{inputs['lobbying_cost']:,.0f}")
    with c3:
        st.metric("EP Passes", f"{int(inputs['ep_passes'])}")

    st.caption(f"Interest: {inputs['interest']}  ·  Country: {inputs['country']}  ·  Members FTE: {inputs['members_fte']}")

    # Scatter plot
    st.divider()
    st.subheader("How does your organization compare?")

    if df_lobbyfacts is not None:
        df_plot = df_lobbyfacts[
            (df_lobbyfacts['Lobbying cost'] > 0) &
            (df_lobbyfacts['Meetings'] > 0)
        ].copy()

        df_plot = df_plot.rename(columns={
            'Lobbying cost': 'lobbying_cost',
            'Meetings': 'meetings',
            'Name': 'name',
        })

        df_plot = df_plot[['name', 'lobbying_cost', 'meetings']].dropna()

        fig = px.scatter(
            df_plot,
            x='lobbying_cost',
            y='meetings',
            hover_name='name',
            log_x=True,
            log_y=True,
            labels={
                'lobbying_cost': 'Lobbying Cost (€, log scale)',
                'meetings': 'EP Meetings (log scale)',
            },
            opacity=0.45,
            color_discrete_sequence=['#4a90d9'],
        )

        fig.add_trace(go.Scatter(
            x=[inputs['lobbying_cost']],
            y=[prediction],
            mode='markers+text',
            marker=dict(size=18, color='#e63946', symbol='star', line=dict(width=1, color='white')),
            text=['Your Org'],
            textposition='top center',
            name='Your Organization',
            hovertemplate=f'<b>Your Organization</b><br>Cost: €{inputs["lobbying_cost"]:,.0f}<br>Predicted Meetings: {prediction:.1f}<extra></extra>',
        ))

        fig.update_layout(height=480, margin=dict(t=20, b=40))
        st.plotly_chart(fig, use_container_width=True)

        # Similar orgs list
        st.divider()
        st.subheader("Similar organizations")
        st.write("Save any of these to compare on the Organization Comparison page.")

        similar = df_plot[
            (df_plot['lobbying_cost'] > inputs['lobbying_cost'] * 0.5) &
            (df_plot['lobbying_cost'] < inputs['lobbying_cost'] * 2.0)
        ].head(5)

        if similar.empty:
            st.info("No similar organizations found in this cost range.")
        else:
            for _, row in similar.iterrows():
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.write(f"**{row['name']}** — €{row['lobbying_cost']:,.0f} · {row['meetings']:.0f} meetings")
                with col_b:
                    if st.button("Save", key=f"save_{row['name']}"):
                        entry = {
                            'name': row['name'],
                            'lobbying_cost': row['lobbying_cost'],
                            'meetings': row['meetings'],
                        }
                        existing = [o['name'] for o in st.session_state.saved_comparisons]
                        if entry['name'] not in existing:
                            if len(st.session_state.saved_comparisons) >= 2:
                                st.session_state.saved_comparisons.pop(0)
                            st.session_state.saved_comparisons.append(entry)
                            st.success(f"Saved **{entry['name']}** — go to Organization Comparison to compare.")
                        else:
                            st.info("Already saved.")
    else:
        st.info("Scatter plot unavailable — lobbyfacts data not found.")