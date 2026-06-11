import logging
logger = logging.getLogger(__name__)
import streamlit as st
from modules.nav import SideBarLinks
import requests

st.set_page_config(layout="wide")
SideBarLinks()

st.title("Party Prediction Demo")
st.write("Use the inputs below to call the party prediction endpoint and display the result on screen.")

country_options = [
    "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czech Republic",
    "Denmark", "Estonia", "Finland", "France", "Germany", "Greece", "Hungary",
    "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg", "Malta",
    "Netherlands", "Poland", "Portugal", "Romania", "Slovenia", "Spain", "Sweden",
]

with st.form("party_prediction_form"):
    col1, col2 = st.columns(2)
    with col1:
        populist = st.select_slider("Party Populist",
                                    ["Not Populist", "Borderline Populist", "Populist"])
        left_right = st.select_slider("Party Left/Right",
                                      ["Left", "Borderline Left", "Neutral", "Borderline Right", "Right"],
                                      value="Neutral")
        eurosceptic = st.select_slider("Party Eurosceptic",
                                       ["Not Eurosceptic", "Borderline Eurosceptic", "Eurosceptic"])
    with col2:
        country = st.selectbox("Country", country_options)
        eu_anti_pro = st.slider("Anti or Pro EU", min_value=0.0, max_value=10.0, step=0.1, value=5.0)
    submitted = st.form_submit_button("Predict")

if submitted:
    payload = {
        "populist":      1 if populist in ("Populist", "Borderline Populist") else 0,
        "populist_bl":   1 if populist == "Borderline Populist" else 0,
        "farright":      1 if left_right in ("Right", "Borderline Right") else 0,
        "farright_bl":   1 if left_right == "Borderline Right" else 0,
        "farleft":       1 if left_right in ("Left", "Borderline Left") else 0,
        "farleft_bl":    1 if left_right == "Borderline Left" else 0,
        "eurosceptic":   1 if eurosceptic in ("Eurosceptic", "Borderline Eurosceptic") else 0,
        "eurosceptic_bl":1 if eurosceptic == "Borderline Eurosceptic" else 0,
        "country_name":  country,
        "eu_anti_pro":   eu_anti_pro,
    }

    api_urls = [
        "http://web-api:4000/party/prediction",
        "http://localhost:4000/party/prediction",
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
        prediction = float(result["prediction"])
        pct = round(prediction * 100, 1)

        st.divider()
        st.subheader("Prediction Result")

        # Determine confidence bucket
        if pct >= 60:
            verdict = "Very likely to hold parliamentary seats"
            color = "green"
            icon = "🟢"
        elif pct >= 40:
            verdict = "Moderate chance of holding parliamentary seats"
            color = "orange"
            icon = "🟡"
        elif pct >= 20:
            verdict = "Unlikely to hold parliamentary seats"
            color = "orange"
            icon = "🟠"
        else:
            verdict = "Very unlikely to hold parliamentary seats"
            color = "red"
            icon = "🔴"

        col_a, col_b = st.columns([1, 2])
        with col_a:
            st.metric(
                label="Party in parliament probability",
                value=f"{pct}%",
                width="stretch"
            )
        with col_b:
            st.markdown(f"### {icon} {verdict}")
            st.markdown(
                f"Based on the selected profile — **{left_right}**, **{populist}**, "
                f"**{eurosceptic}**, EU stance **{eu_anti_pro}/10** in **{country}** — "
                f"the model estimates a **{pct}% probability** of this party group "
                f"securing parliamentary representation."
            )

        st.divider()

    else:
        st.error(f"Prediction request failed: {last_error}")