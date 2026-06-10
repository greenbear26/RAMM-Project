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
st.write("Enter your organization's details below to predict how many EP meetings it is likely to secure.")

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

# Session state for saved comparisons
if "saved_comparisons" not in st.session_state:
    st.session_state.saved_comparisons = []

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
        lobbying_cost = st.number_input("Lobbying cost (€)", min_value=0.0, step=1000.0, value=10000.0)
        ep_passes = st.number_input("EP passes", min_value=0.0, step=1.0, value=10.0)
        members_fte = st.number_input("Members FTE", min_value=0.0, step=1.0, value=25.0)

    with col2:
        country = st.selectbox("Country", country_options)
        interest = st.selectbox("Interest representation", interest_options)

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
        prediction = result["prediction"]

        st.divider()
        st.subheader("Prediction Result")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Predicted EP Meetings", f"{prediction:.1f}")
        with c2:
            st.metric("Lobbying Cost", f"€{lobbying_cost:,.0f}")
        with c3:
            st.metric("EP Passes", f"{int(ep_passes)}")

        st.caption(f"Interest: {interest}  ·  Country: {country}  ·  Members FTE: {members_fte}")

        # Scatter plot
        st.divider()
        st.subheader("How does your organization compare?")
        st.write("Click any dot to save that organization to your comparisons.")

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

            # Add predicted org as a red star
            fig.add_trace(go.Scatter(
                x=[lobbying_cost],
                y=[prediction],
                mode='markers+text',
                marker=dict(size=18, color='#e63946', symbol='star', line=dict(width=1, color='white')),
                text=['Your Org'],
                textposition='top center',
                name='Your Organization',
                hovertemplate=f'<b>Your Organization</b><br>Cost: €{lobbying_cost:,.0f}<br>Predicted Meetings: {prediction:.1f}<extra></extra>',
            ))

            fig.update_layout(
                height=480,
                margin=dict(t=20, b=40),
            )

            selected = st.plotly_chart(fig, use_container_width=True, on_select='rerun', key='scatter')

            # Handle click to save to comparisons
            if selected and selected.get('selection') and selected['selection'].get('points'):
                pts = selected['selection']['points']
                if pts:
                    clicked_idx = pts[0].get('point_index')
                    if clicked_idx is not None and clicked_idx < len(df_plot):
                        clicked_org = df_plot.iloc[clicked_idx]
                        org_entry = {
                            'name': clicked_org['name'],
                            'lobbying_cost': clicked_org['lobbying_cost'],
                            'meetings': clicked_org['meetings'],
                        }
                        existing_names = [o['name'] for o in st.session_state.saved_comparisons]
                        if org_entry['name'] not in existing_names:
                            if len(st.session_state.saved_comparisons) >= 2:
                                st.session_state.saved_comparisons.pop(0)
                            st.session_state.saved_comparisons.append(org_entry)
                            st.success(f"Saved **{org_entry['name']}** to comparisons.")
                        else:
                            st.info(f"**{org_entry['name']}** is already saved.")

            # Save predicted org button
            st.divider()
            if st.button("Save my predicted organization to comparisons"):
                entry = {
                    'name': f'Your Org (predicted, €{lobbying_cost:,.0f})',
                    'lobbying_cost': lobbying_cost,
                    'meetings': prediction,
                }
                existing_names = [o['name'] for o in st.session_state.saved_comparisons]
                if entry['name'] not in existing_names:
                    if len(st.session_state.saved_comparisons) >= 2:
                        st.session_state.saved_comparisons.pop(0)
                    st.session_state.saved_comparisons.append(entry)
                    st.success("Saved! Head to **Organization Comparison** to compare.")
                else:
                    st.info("Already saved.")
        else:
            st.info("Scatter plot unavailable — lobbyfacts data not found.")



