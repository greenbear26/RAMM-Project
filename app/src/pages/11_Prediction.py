import logging

logger = logging.getLogger(__name__)

import streamlit as st
from modules.nav import SideBarLinks
import requests

st.set_page_config(layout="wide")

# Display the appropriate sidebar links for the role of the logged in user
SideBarLinks()

st.title("Lobby Prediction Demo")
st.write("Use the inputs below to call the lobbying prediction endpoint and display the result on screen.")

country_options = [
    "Austria",
    "Belgium",
    "Bulgaria",
    "Croatia",
    "Cyprus",
    "Czech Republic",
    "Denmark",
    "Estonia",
    "Finland",
    "France",
    "Germany",
    "Greece",
    "Hungary",
    "Ireland",
    "Italy",
    "Latvia",
    "Lithuania",
    "Luxembourg",
    "Malta",
    "Netherlands",
    "Poland",
    "Portugal",
    "Romania",
    "Slovenia",
    "Spain",
    "Sweden",
]

interest_options = [
    "Advances interests of their clients",
    "Does not represent commercial interests",
    "Promotes their own interests or the collective interests of their members",
]

with st.form("lobby_prediction_form"):
    col1, col2 = st.columns(2)

    with col1:
        lobbying_cost = st.number_input("Lobbying cost", min_value=0.0, step=1000.0, value=10000.0)
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
    elif response.ok:
        result = response.json()
        st.subheader("Prediction Result")
        st.metric("Predicted value", result["prediction"])
        st.write("Inputs used for the prediction:")
        st.json(result["input_variables"])
    else:
        st.error(f"Prediction request failed: {last_error}")




