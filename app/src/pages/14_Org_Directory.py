import logging
logger = logging.getLogger(__name__)

import streamlit as st
import requests
import pandas as pd
from modules.nav import SideBarLinks

st.set_page_config(page_title="Researcher Home", page_icon="📊", layout='wide')

SideBarLinks()

st.markdown("# Organization Comparison")
st.sidebar.header("Researcher Home")
st.write("Save organizations from the Add New Organization page or the Meeting Prediction page, then select two here to compare their lobbying spend, policy areas, and ML influence scores side by side.")

# Session state
if "saved_orgs" not in st.session_state:
    st.session_state.saved_orgs = []
if "saved_comparisons" not in st.session_state:
    st.session_state.saved_comparisons = []
if "compare_pair" not in st.session_state:
    st.session_state.compare_pair = []

# Merge saved_orgs and saved_comparisons into one list for display
# saved_orgs come from Add New Organization (have org_id)
# saved_comparisons come from the scatter plot (no org_id)
all_saved = st.session_state.saved_orgs.copy()
for org in st.session_state.saved_comparisons:
    existing_names = [o.get('name') for o in all_saved]
    if org.get('name') not in existing_names:
        all_saved.append(org)

# Layout
main_col, saved_col = st.columns([3, 1])

# RIGHT COLUMN — Saved Comparisons
with saved_col:
    st.markdown("### Saved Comparisons")
    st.caption("Select up to 2 orgs to compare.")

    if not all_saved:
        st.info("No saved orgs yet. Use the **Add New Organization** page or click a dot on the **Meeting Prediction** page.")
    else:
        for org in all_saved:
            org_id = org.get("org_id")
            in_compare = org.get("name") in [o.get("name") for o in st.session_state.compare_pair]
            border = "#2563EB" if in_compare else "#E0D8C8"
            check = "✅ " if in_compare else ""
            st.markdown(f"""
            <div style="border: 2px solid {border}; border-radius: 10px;
                        padding: 10px 14px; margin-bottom: 8px; background: #fff;">
              <div style="font-weight: 500; font-size: 13px; color: #1A1A1A;">{check}{org['name']}</div>
              <div style="font-size: 11px; color: #999; margin-top: 2px;">
                {org.get('country_code', '—')} &nbsp;·&nbsp; €{org.get('lobbying_cost', 0):,.0f}
              </div>
            </div>""", unsafe_allow_html=True)

            b1, b2 = st.columns(2)
            with b1:
                cmp_label = "✕ Remove" if in_compare else "Compare"
                if st.button(cmp_label, key=f"cmp_{org['name']}", use_container_width=True):
                    if in_compare:
                        st.session_state.compare_pair = [
                            o for o in st.session_state.compare_pair
                            if o.get("name") != org.get("name")
                        ]
                    else:
                        if len(st.session_state.compare_pair) < 2:
                            st.session_state.compare_pair.append(org)
                        else:
                            st.warning("Max 2 orgs. Remove one first.")
                    st.rerun()
            with b2:
                if st.button("🗑️", key=f"del_{org['name']}", use_container_width=True):
                    st.session_state.saved_orgs = [
                        o for o in st.session_state.saved_orgs
                        if o.get("name") != org.get("name")
                    ]
                    st.session_state.saved_comparisons = [
                        o for o in st.session_state.saved_comparisons
                        if o.get("name") != org.get("name")
                    ]
                    st.session_state.compare_pair = [
                        o for o in st.session_state.compare_pair
                        if o.get("name") != org.get("name")
                    ]
                    st.rerun()

# LEFT COLUMN — Score Comparison
with main_col:
    st.tabs(["📊 Score Comparison"])

    if len(st.session_state.compare_pair) == 0:
        st.info("Use the **Add New Organization** page to save orgs, then select 2 from the right column to compare.")

    elif len(st.session_state.compare_pair) == 1:
        st.info("Select one more org from your saved list on the right to compare.")

    else:
        org1 = st.session_state.compare_pair[0]
        org2 = st.session_state.compare_pair[1]

        st.text_input("Filter policy area shown in charts (optional)", placeholder="e.g. Climate")

        col1, col2 = st.columns(2)

        for col, org in [(col1, org1), (col2, org2)]:
            with col:
                org_id = org.get("org_id")

                # If org came from scatter plot (no org_id), just show what we have
                if org_id:
                    try:
                        r = requests.get(f"http://web-api:4000/organizations/{org_id}")
                        details = r.json() if r.status_code == 200 else org
                    except:
                        details = org
                else:
                    details = org

                st.markdown(f"#### {details.get('name', org['name'])}")
                st.markdown(f"**Spend:** &nbsp; €{details.get('lobbying_cost', 0):,.0f}")

                if org_id:
                    activities = details.get("lobbying_activities", [])
                    area_names = [a.get("eu_institution", "—") for a in activities[:3]]
                    st.markdown(f"**Policy Areas:** &nbsp; {', '.join(area_names) if area_names else '—'}")

                    try:
                        ml_r = requests.get(
                            f"http://web-api:4000/organizations/{org_id}/influence-prediction"
                        )
                        if ml_r.status_code == 200:
                            ml = ml_r.json()
                            score = ml.get("influence_score", "—")
                            cls = ml.get("influence_class", "")
                            st.markdown(f"**ML Score:** &nbsp; `{score}` &nbsp; *{cls}*")
                        else:
                            st.markdown("**ML Score:** &nbsp; —")
                    except:
                        st.markdown("**ML Score:** &nbsp; *(backend not connected)*")

                    expenditures = details.get("expenditures", [])
                    if expenditures:
                        df = pd.DataFrame(expenditures)
                        if "year" in df.columns and "amount_eur" in df.columns:
                            df = df[["year", "amount_eur"]].dropna().sort_values("year")
                            st.bar_chart(df.set_index("year")["amount_eur"], use_container_width=True)
                    else:
                        st.caption("No expenditure data available for chart.")
                else:
                    # Org from scatter plot — show what we have
                    st.markdown(f"**EP Meetings:** &nbsp; {org.get('meetings', '—')}")
                    st.caption("This organization was saved from the Meeting Prediction scatter plot.")