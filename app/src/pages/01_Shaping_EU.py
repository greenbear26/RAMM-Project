import logging
logger = logging.getLogger(__name__)

import streamlit as st
import requests
import pandas as pd
from pathlib import Path
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

SideBarLinks()

st.markdown("# Who is Shaping EU Policies?")
st.sidebar.header("Citizen View")
st.write("Pick your areas of interest and we'll show you which organizations are lobbying on them.")

# Session state 
if "selected_policies" not in st.session_state:
    st.session_state.selected_policies = []
if "selected_countries" not in st.session_state:
    st.session_state.selected_countries = []

POLICIES = [
    "Artificial Intelligence", "Climate & Energy", "Healthcare",
    "Defence & Security", "Finance & Banking", "Agriculture",
    "Digital Markets", "Transport",
]

COUNTRIES = [
    "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus",
    "Czech Republic", "Denmark", "Estonia", "Finland", "France",
    "Germany", "Greece", "Hungary", "Ireland", "Italy",
    "Latvia", "Lithuania", "Luxembourg", "Malta", "Netherlands",
    "Poland", "Portugal", "Romania", "Slovakia", "Slovenia",
    "Spain", "Sweden",
]


POLICY_KEYWORDS = {
    "Artificial Intelligence": ["AI", "artificial intelligence", "digital", "technology", "software"],
    "Climate & Energy":        ["climate", "energy", "environment", "green", "renewable", "emission"],
    "Healthcare":              ["health", "pharma", "medical", "hospital", "medicine", "biotech"],
    "Defence & Security":      ["defence", "defense", "security", "military", "nato"],
    "Finance & Banking":       ["finance", "banking", "financial", "investment", "insurance", "capital"],
    "Agriculture":             ["agriculture", "farming", "food", "rural", "crop", "livestock"],
    "Digital Markets":         ["digital", "platform", "online", "internet", "e-commerce", "data"],
    "Transport":               ["transport", "mobility", "aviation", "rail", "shipping", "logistics"],
}

# Load datasets 
@st.cache_data
def load_lobbyfacts():
    df = pd.read_csv("/appcode/datasets/lobbying/lobbyfacts_cleaned.csv")
    df = df.dropna(subset=["Name", "Lobbying cost", "Head office"])
    return df

@st.cache_data
def load_worldbank():
    df = pd.read_csv("/appcode/datasets/GDP_Energy_WBdat.csv")
    return df

lf_df = load_lobbyfacts()
wb_df = load_worldbank()

# Pick a Policy 
st.markdown("### Pick a Policy")
col1, col2 = st.columns([4, 1])
with col1:
    selected_policy = st.selectbox(
        "Policy", ["-- Select --"] + POLICIES,
        label_visibility="collapsed"
    )
with col2:
    add_policy = st.button("Add", key="add_pol", use_container_width=True)

if add_policy and selected_policy != "-- Select --":
    if selected_policy not in st.session_state.selected_policies:
        st.session_state.selected_policies.append(selected_policy)
        st.rerun()

if st.session_state.selected_policies:
    pc1, pc2 = st.columns([4, 1])
    with pc1:
        st.markdown("**Selected:** " + "  ".join(
            [f"`{p}`" for p in st.session_state.selected_policies]
        ))
    with pc2:
        if st.button("Clear", key="clear_pol", use_container_width=True):
            st.session_state.selected_policies = []
            st.rerun()

st.markdown("---")

# Pick a Country
st.markdown("### Pick a Country")
col3, col4 = st.columns([4, 1])
with col3:
    selected_country = st.selectbox(
        "Country", ["-- Select --"] + COUNTRIES,
        label_visibility="collapsed"
    )
with col4:
    add_country = st.button("Add", key="add_cty", use_container_width=True)

if add_country and selected_country != "-- Select --":
    if selected_country not in st.session_state.selected_countries:
        st.session_state.selected_countries.append(selected_country)
        st.rerun()

if st.session_state.selected_countries:
    cc1, cc2 = st.columns([4, 1])
    with cc1:
        st.markdown("**Selected:** " + "  ".join(
            [f"`{c}`" for c in st.session_state.selected_countries]
        ))
    with cc2:
        if st.button("Clear", key="clear_cty", use_container_width=True):
            st.session_state.selected_countries = []
            st.rerun()

st.markdown("---")

# Sidebar summary 
st.sidebar.markdown("### Your Selections")
st.sidebar.markdown("**Policies:** " + (", ".join(st.session_state.selected_policies) or "None"))
st.sidebar.markdown("**Countries:** " + (", ".join(st.session_state.selected_countries) or "None"))

# Submit 
if st.button("Submit Search Preferences", type="primary", use_container_width=True):
    if not st.session_state.selected_policies and not st.session_state.selected_countries:
        st.warning("Please select at least one policy or country before submitting.")
    else:
        # Save preferences to DB
        prefs = {
            "user_id":    st.session_state.get("user_id", 1),
            "query_json": str({
                "policies":  st.session_state.selected_policies,
                "countries": st.session_state.selected_countries,
            }),
            "file_format": "json",
        }
        try:
            requests.post("http://web-api:4000/preferences", json=prefs)
        except:
            pass

        st.markdown("## Results")

        # Filter
        filtered = lf_df.copy()

        # Filter by country — matches "Head office" column
        if st.session_state.selected_countries:
            filtered = filtered[
                filtered["Head office"].isin(st.session_state.selected_countries)
            ]

        # Filter by policy — keyword match on "Interest represented" column
        if st.session_state.selected_policies:
            keywords = []
            for policy in st.session_state.selected_policies:
                keywords.extend(POLICY_KEYWORDS.get(policy, [policy.lower()]))
            pattern = "|".join(keywords)
            filtered = filtered[
                filtered["Interest represented"].str.contains(
                    pattern, case=False, na=False
                )
            ]

        # Display results 
        if not filtered.empty:
            st.markdown(f"### 🏛️ Organizations ({len(filtered)} found)")
            st.dataframe(
                filtered[[
                    "Name", "Head office", "Lobbying cost",
                    "Interest represented", "Meetings", "all EP passes"
                ]].rename(columns={
                    "Name":                 "Organization",
                    "Head office":          "Country",
                    "Lobbying cost":        "Lobbying Cost (€)",
                    "Interest represented": "Interest",
                    "Meetings":             "EU Meetings",
                    "all EP passes":        "EP Passes",
                }).sort_values("Lobbying Cost (€)", ascending=False),
                use_container_width=True
            )

            # Top spender callout
            top = filtered.nlargest(1, "Lobbying cost").iloc[0]
            st.info(
                f"💡 Top spender from your selection: **{top['Name']}** "
                f"({top['Head office']}) — €{top['Lobbying cost']:,.0f}"
            )
        else:
            st.info("No organizations found for your selections. Try different filters.")

        # World Bank indicators for selected countries 
        if st.session_state.selected_countries:
            st.markdown("### 🌍 Country Economic Context")
            st.caption("GDP, fossil fuel usage, and CO2 emissions from World Bank data.")

            for country in st.session_state.selected_countries:
                country_data = wb_df[wb_df["country"] == country].sort_values("date")
                if not country_data.empty:
                    st.markdown(f"**{country}**")
                    latest = country_data.iloc[-1]
                    m1, m2, m3 = st.columns(3)
                    m1.metric("GDP (USD)",         f"${latest['GDP']:,.0f}")
                    m2.metric("Fossil Fuels (%)",  f"{latest['Fossil_Fuels']:.1f}%")
                    m3.metric("CO2 Emissions",     f"{latest['CO2_emit']:,.0f} kt")
                    st.line_chart(
                        country_data.set_index("date")["GDP"],
                        use_container_width=True,
                        height=150
                    )