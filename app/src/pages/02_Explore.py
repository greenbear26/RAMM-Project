import logging
logger = logging.getLogger(__name__)

import streamlit as st
import requests
import pandas as pd
import random
from pathlib import Path
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

SideBarLinks()

st.sidebar.header("Citizen Home")

# Session state
if "your_topics" not in st.session_state:
    st.session_state.your_topics = []
if "saved_facts" not in st.session_state:
    st.session_state.saved_facts = []

# Load dataset 
DATA_PATH = Path("/appcode/datasets/lobbying/lobbyfacts_cleaned.csv")

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=["Name", "Lobbying cost", "Head office"])
    return df

df = load_data()

# Generate random facts — only once per session 
def generate_facts(df, n=5):
    sample = df.sample(n=n)
    facts = []
    for _, row in sample.iterrows():
        name     = row["Name"]
        cost     = row["Lobbying cost"]
        country  = row["Head office"]
        meetings = row["Meetings"]
        passes   = row["all EP passes"]

        if cost >= 1_000_000:
            cost_str = f"€{cost/1_000_000:.1f}M"
        else:
            cost_str = f"€{cost:,.0f}"

        templates = [
            f"**{name}** ({country}) spent **{cost_str}** lobbying the EU and held **{int(meetings) if pd.notna(meetings) else 'unknown'}** meetings with EU officials.",
            f"**{name}**, headquartered in {country}, has **{int(passes) if pd.notna(passes) else 'unknown'}** EP access passes and spends **{cost_str}** per year on lobbying.",
            f"Did you know? **{name}** from {country} is one of the organizations actively lobbying the EU, spending **{cost_str}** annually.",
            f"**{name}** ({country}) logged **{int(meetings) if pd.notna(meetings) else 'unknown'}** meetings with EU institutions and holds **{int(passes) if pd.notna(passes) else 'unknown'}** EP access passes.",
        ]
        facts.append(random.choice(templates))
    return facts


if "facts" not in st.session_state:
    st.session_state.facts = generate_facts(df, n=5)

facts = st.session_state.facts

EXPLORE_TOPICS = [
    {"topic": "Artificial Intelligence", "desc": "See which tech giants and startups are shaping EU AI regulation."},
    {"topic": "Climate & Energy",        "desc": "Discover who is lobbying on the Green Deal and energy transition."},
    {"topic": "Healthcare",              "desc": "Explore pharmaceutical and healthcare lobbying across the EU."},
    {"topic": "Finance & Banking",       "desc": "Find out which financial institutions influence EU banking rules."},
    {"topic": "Defence & Security",      "desc": "See lobbying activity around EU defence and security policy."},
]

# Layout 
main_col, saved_col = st.columns([2.5, 1])

with main_col:

    # Search bar 
    query = st.text_input("Search", placeholder="🔍  Search a topic or policy...",
                          label_visibility="collapsed")
    search_clicked = st.button("Search", type="primary")

    if search_clicked and query:
        if query not in st.session_state.your_topics:
            st.session_state.your_topics.append(query)
        try:
            resp = requests.get("http://web-api:4000/organizations",
                                params={"policy_area": query})
            results = resp.json() if resp.status_code == 200 else []
        except:
            results = []
            st.warning("⚠️ Backend not connected yet.")

        if results:
            st.success(f"Found **{len(results)} organizations** lobbying on *{query}*")
            for org in results[:5]:
                st.markdown(f"**{org.get('name','—')}** — {org.get('country_code','—')} · €{org.get('lobbying_cost',0):,.0f}")
        else:
            st.info(f"No results found for '{query}'.")

   
    if st.session_state.your_topics:
        tc1, tc2 = st.columns([4, 1])
        with tc1:
            st.markdown("**Your topics:** " + "  ".join(
                [f"`{t}`" for t in st.session_state.your_topics]
            ))
        with tc2:
            if st.button("Clear topics", use_container_width=True):
                st.session_state.your_topics = []
                st.rerun()

    st.markdown("---")

   
    
    fact_title, fact_btn = st.columns([3, 1])
    with fact_title:
        st.markdown("### Did you know? — Top Facts")
    with fact_btn:
        if st.button("🔄 Refresh Facts", use_container_width=True):
            st.session_state.facts = generate_facts(df, n=5)
            st.rerun()
    st.caption("Facts are pulled from real EU lobbying data and refreshed every time you visit.")   

    for i, fact in enumerate(facts):
        with st.container():
            fc1, fc2 = st.columns([5, 1])
            with fc1:
                st.markdown(f"> {fact}")
            with fc2:
                if st.button("Save", key=f"save_fact_{i}", use_container_width=True):
                    if fact not in st.session_state.saved_facts:
                        st.session_state.saved_facts.append(fact)
                        st.rerun()

    st.markdown("---")


    st.markdown("### Explore Topics")
    for topic in EXPLORE_TOPICS:
        with st.container():
            t1, t2 = st.columns([4, 1])
            with t1:
                st.markdown(f"**{topic['topic']}**")
                st.caption(topic["desc"])
            with t2:
                if st.button("Explore", key=f"explore_{topic['topic']}", use_container_width=True):
                    if topic["topic"] not in st.session_state.your_topics:
                        st.session_state.your_topics.append(topic["topic"])
                    st.rerun()

with saved_col:
    st.markdown("### 🔖 Saved Facts")
    if not st.session_state.saved_facts:
        st.info("No saved facts yet. Hit Save on any fact to keep it here.")
    else:
        for i, fact in enumerate(st.session_state.saved_facts):
            with st.container():
                st.markdown(f"> {fact}")
                if st.button("Remove", key=f"remove_fact_{i}", use_container_width=True):
                    st.session_state.saved_facts.pop(i)
                    st.rerun()