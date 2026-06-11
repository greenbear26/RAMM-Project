import logging
logger = logging.getLogger(__name__)

import html
import re
import random
import requests
import streamlit as st
import streamlit.components.v1 as components
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

SideBarLinks()

st.sidebar.header("Citizen Home")

API_BASE = "http://web-api:4000"

if "saved_facts" not in st.session_state:
    st.session_state.saved_facts = []


def fetch_random_orgs(n=10):
    try:
        resp = requests.get(f"{API_BASE}/organizations/random", params={"n": n}, timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []


def generate_facts(n=10):
    orgs = fetch_random_orgs(n)
    facts = []
    for org in orgs:
        name     = org.get("name", "Unknown")
        cost     = org.get("lobbying_cost") or 0
        country  = org.get("country_name", "Unknown")
        meetings = org.get("ep_meetings")
        passes   = org.get("all_ep_passes")

        cost_str = f"€{cost/1_000_000:.1f}M" if cost >= 1_000_000 else f"€{cost:,.0f}"
        meetings_str = str(int(meetings)) if meetings is not None else "unknown"
        passes_str   = str(int(passes))   if passes   is not None else "unknown"

        templates = [
            f"**{name}** ({country}) spent **{cost_str}** lobbying the EU and held **{meetings_str}** meetings with EU officials.",
            f"**{name}**, headquartered in {country}, has **{passes_str}** EP access passes and spends **{cost_str}** per year on lobbying.",
            f"Did you know? **{name}** from {country} is one of the organizations actively lobbying the EU, spending **{cost_str}** annually.",
            f"**{name}** ({country}) logged **{meetings_str}** meetings with EU institutions and holds **{passes_str}** EP access passes.",
        ]
        facts.append(random.choice(templates))
    return facts


if "facts" not in st.session_state:
    st.session_state.facts = generate_facts(n=10)

facts = st.session_state.facts


def strip_markdown(text):
    return re.sub(r'\*+', '', text)


def clipboard_button(fact_text):
    plain = html.escape(strip_markdown(fact_text), quote=True)
    components.html(
        f"""
        <button
            data-txt="{plain}"
            onclick="
                navigator.clipboard.writeText(this.dataset.txt)
                    .then(() => {{ this.textContent = 'Copied!'; setTimeout(() => this.textContent = 'Copy', 1500); }})
                    .catch(() => {{ this.textContent = 'Failed'; }});
            "
            style="
                width:100%; padding:6px 0; cursor:pointer;
                background:#1E3A5F; color:#fff;
                border:1px solid #334155; border-radius:6px;
                font-size:12px; font-family:sans-serif;
            ">
            Copy
        </button>
        """,
        height=38,
    )


main_col, saved_col = st.columns([2.5, 1])

with main_col:
    st.markdown("""
Browse randomly generated facts drawn from real EU lobbying data. Hit **Save** on any fact
to pin it to your saved list, then use **Copy** to paste it anywhere you like.
""")

    fact_title, fact_btn = st.columns([3, 1])
    with fact_title:
        st.markdown("### Did you know? — EU Lobbying Facts")
    with fact_btn:
        if st.button("Refresh Facts", use_container_width=True):
            st.session_state.facts = generate_facts(n=10)
            st.rerun()
    st.caption("Facts are pulled from real EU lobbying data. Refresh for a new set.")

    st.markdown("")
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

with saved_col:
    st.markdown("### Saved Facts")
    if not st.session_state.saved_facts:
        st.info("No saved facts yet. Hit Save on any fact to keep it here.")
    else:
        for i, fact in enumerate(st.session_state.saved_facts):
            with st.container():
                st.markdown(f"> {fact}")
                clipboard_button(fact)
                if st.button("Remove", key=f"remove_fact_{i}", use_container_width=True):
                    st.session_state.saved_facts.pop(i)
                    st.rerun()
                st.markdown("---")
