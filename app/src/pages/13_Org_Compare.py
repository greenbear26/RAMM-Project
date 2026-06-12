import logging
logger = logging.getLogger(__name__)

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from modules.nav import SideBarLinks
import ast

st.set_page_config(page_title="Organization Comparison", page_icon="📊", layout='wide')

SideBarLinks()

st.markdown("# Organization Comparison")
st.sidebar.header("Researcher Home")

st.markdown("""
Select two saved organizations to compare them side by side. View lobbying spend, meeting counts,
policy area overlap, and lobbying efficiency to understand how each organization stacks up.
Save organizations first from the **Search Organizations** page.
""")

if "saved_orgs" not in st.session_state:
    st.session_state.saved_orgs = []
if "saved_comparisons" not in st.session_state:
    st.session_state.saved_comparisons = []
if "compare_pair" not in st.session_state:
    st.session_state.compare_pair = []

all_saved = st.session_state.saved_orgs.copy()
for org in st.session_state.saved_comparisons:
    if org.get('name') not in [o.get('name') for o in all_saved]:
        all_saved.append(org)

main_col, saved_col = st.columns([3, 1])

# RIGHT COLUMN — saved org list
with saved_col:
    st.markdown("### Saved Organizations")
    st.caption("Select up to 2 orgs to compare.")

    if not all_saved:
        st.info("No saved orgs yet. Use the **Search Organizations** page or click through the **ML Influence Prediction** page to save orgs there.")
    else:
        for org in all_saved:
            in_compare = org.get("name") in [o.get("name") for o in st.session_state.compare_pair]
            border = "#2563EB" if in_compare else "#E0D8C8"
            check = "✅ " if in_compare else ""
            st.markdown(f"""
            <div style="border: 2px solid {border}; border-radius: 10px;
                        padding: 10px 14px; margin-bottom: 8px; background: #1A1F2E;">
              <div style="font-weight: 500; font-size: 13px; color: #FFFFFF;">{check}{org['name']}</div>
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

# LEFT COLUMN — comparison view
with main_col:
    tab1, = st.tabs(["📊 Score Comparison"])

    with tab1:
        if len(st.session_state.compare_pair) == 0:
            st.info("Use the **Search Organizations** page to save orgs, then select 2 from the right column to compare.")

        elif len(st.session_state.compare_pair) == 1:
            st.info("Select one more org from your saved list on the right to compare.")

        else:
            org1 = st.session_state.compare_pair[0]
            org2 = st.session_state.compare_pair[1]

            # ── Fetch all data up front so we can build cross-org charts ──────
            pair_data = []
            for org in [org1, org2]:
                org_id = org.get("org_id")
                details = org.copy()
                if org_id:
                    try:
                        r = requests.get(f"http://web-api:4000/organizations/{org_id}")
                        if r.status_code == 200:
                            details = r.json()
                    except Exception:
                        pass
                pair_data.append({"details": details})

            d1, d2 = pair_data[0], pair_data[1]
            name1 = d1["details"].get("name", org1["name"])
            name2 = d2["details"].get("name", org2["name"])

            # Chart 1: Side-by-side spend, meetings, EP passes
            st.markdown("### At a Glance")
            spend1  = d1["details"].get("lobbying_cost") or 0
            spend2  = d2["details"].get("lobbying_cost") or 0
            members1 = d1["details"].get("members_fte") or 0
            members2 = d2["details"].get("members_fte") or 0
            meet1   = d1["details"].get("ep_meetings") or 0
            meet2   = d2["details"].get("ep_meetings") or 0

            fig_bar = go.Figure(data=[
                go.Bar(name=name1, x=["Lobbying Spend (M€)", "European Commission Meetings", "Full-time Employees"],
                       y=[spend1 / 1000000, meet1, members1],
                       marker_color="#2563EB"),
                go.Bar(name=name2, x=["Lobbying Spend (M€)", "European Commission Meetings", "Full-time Employees"],
                       y=[spend2 / 1000000, meet2, members2],
                       marker_color="#F59E0B"),
            ])
            fig_bar.update_layout(
                barmode="group",
                height=320,
                margin=dict(t=20, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            st.divider()

            # Chart 3: Policy area overlap 
            st.markdown("### Policy Area Overlap")

            areas1 = set(ast.literal_eval(d1["details"].get("policy_areas") or "[]"))
            areas2 = set(ast.literal_eval(d2["details"].get("policy_areas") or "[]"))
            
            shared    = sorted(areas1 & areas2)

            oc1, oc2 = st.columns(2)
            with oc1:
                st.markdown(f"**{name1[:20]}** ({len(areas1)})")
                for a in areas1:
                    # if a in shared:
                    #     st.markdown(f"- **{a}**")
                    # else:
                    st.markdown(f"- {a}")
                if not areas1:
                    st.caption("—")
            with oc2:
                st.markdown(f"**{name2[:20]}** ({len(areas2)})")
                for a in areas2:
                    # if a in shared:
                    #     st.markdown(f"- **{a}**")
                    # else:
                    st.markdown(f"- {a}")
                if not areas2:
                    st.caption("—")
            
            st.markdown(f"**Shared policy areas ({len(shared)})**: {', '.join(shared) if shared else '—'}")

            st.divider()

            #  Chart 4: Efficiency — lobbying cost per EP meeting 
            st.markdown("### Lobbying Efficiency")

            # Cast to float to handle MySQL Decimal and None types safely
            spend1_f = float(spend1) if spend1 else 0.0
            spend2_f = float(spend2) if spend2 else 0.0
            meet1_f  = float(meet1)  if meet1  else 0.0
            meet2_f  = float(meet2)  if meet2  else 0.0

            eff1 = (spend1_f / meet1_f) if meet1_f > 0 else None
            eff2 = (spend2_f / meet2_f) if meet2_f > 0 else None

            ec1, ec2 = st.columns(2)
            with ec1:
                st.markdown(f"**{name1[:30]}**")
                st.metric("Cost per Meeting", f"€{eff1:,.0f}" if eff1 is not None else "—")
                st.metric("Total Spend", f"€{spend1_f:,.0f}")
                st.metric("European Commission Meetings", int(meet1_f) if meet1_f > 0 else "—")
                fte1 = float(d1["details"].get("members_fte") or 0)
                if fte1 > 0:
                    st.metric("Spend per Employee", f"€{spend1_f / fte1:,.0f}")
            with ec2:
                st.markdown(f"**{name2[:30]}**")
                st.metric("Cost per Meeting", f"€{eff2:,.0f}" if eff2 is not None else "—")
                st.metric("Total Spend", f"€{spend2_f:,.0f}")
                st.metric("European Commission Meetings", int(meet2_f) if meet2_f > 0 else "—")
                fte2 = float(d2["details"].get("members_fte") or 0)
                if fte2 > 0:
                    st.metric("Spend per Employee", f"€{spend2_f / fte2:,.0f}")

            if eff1 is not None and eff2 is not None:
                fig_eff = go.Figure(data=[
                    go.Bar(
                        x=[name1[:20], name2[:20]],
                        y=[eff1, eff2],
                        marker_color=["#2563EB", "#F59E0B"],
                        text=[f"€{eff1:,.0f}", f"€{eff2:,.0f}"],
                        textposition="outside",
                    )
                ])
                fig_eff.update_layout(
                    title="Cost per EP Meeting (lower = more efficient)",
                    height=300,
                    margin=dict(t=40, b=20),
                    yaxis_title="€ per meeting",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    showlegend=False,
                )
                st.plotly_chart(fig_eff, use_container_width=True)
