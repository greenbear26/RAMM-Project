import logging
logger = logging.getLogger(__name__)

import streamlit as st
import pandas as pd
import ast
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')
SideBarLinks()

st.markdown("# Who is Shaping EU Policies?")
st.sidebar.header("Citizen View")
st.write("Pick your areas of interest and we'll show you which organizations are lobbying on them.")

@st.cache_data
def load_data():
    df = pd.read_csv('/appcode/lobbyfacts_with_policies.csv')
    df['policy_areas'] = df['policy_areas'].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else []
    )
    return df

df = load_data()

if "selected_policies" not in st.session_state:
    st.session_state.selected_policies = []
if "selected_countries" not in st.session_state:
    st.session_state.selected_countries = []

POLICIES = [
    "Artificial Intelligence",
    "Climate & Energy",
    "Healthcare",
    "Defence & Security",
    "Finance & Banking",
    "Agriculture",
    "Digital Markets",
    "Transport",
]

COUNTRIES = [
    "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus",
    "Czech Republic", "Denmark", "Estonia", "Finland", "France",
    "Germany", "Greece", "Hungary", "Ireland", "Italy", "Latvia",
    "Lithuania", "Luxembourg", "Malta", "Netherlands", "Poland",
    "Portugal", "Romania", "Slovakia", "Slovenia", "Spain", "Sweden",
]

st.markdown("### Pick Policies")
selected_policies = st.multiselect(
    "Select one or more policy areas:",
    options=POLICIES,
    default=st.session_state.selected_policies,
)
st.session_state.selected_policies = selected_policies

st.markdown("---")

st.markdown("### Pick a Country")
selected_countries = st.multiselect(
    "Select one or more countries:",
    options=COUNTRIES,
    default=st.session_state.selected_countries,
)
st.session_state.selected_countries = selected_countries

st.markdown("---")

st.sidebar.markdown("### Your Selections")
st.sidebar.markdown("**Policies:** " + (", ".join(selected_policies) or "None"))
st.sidebar.markdown("**Countries:** " + (", ".join(selected_countries) or "None"))

if st.button("Search", type="primary", use_container_width=True):
    if not selected_policies and not selected_countries:
        st.warning("Please select at least one policy or country.")
    else:
        results = df.copy()

        if selected_policies:
            results = results[results['policy_areas'].apply(
                lambda areas: any(p in areas for p in selected_policies)
            )]

        if selected_countries:
            results = results[results['Head office'].isin(selected_countries)]

        results = results.sort_values('Lobbying cost', ascending=False)

        st.markdown(f"### Results: {len(results)} organizations found")

        if len(results) == 0:
            st.info("No organizations found. Try different filters.")
        else:
            display_cols = ['Name', 'Lobbying cost', 'Meetings', 'all EP passes', 'Interest represented', 'Head office']
            display_cols = [c for c in display_cols if c in results.columns]
            st.dataframe(
                results[display_cols].reset_index(drop=True),
                use_container_width=True
            )