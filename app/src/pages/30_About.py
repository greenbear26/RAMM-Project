import streamlit as st
from PIL import Image
from pathlib import Path
from modules.nav import SideBarLinks

STATIC = Path(__file__).parent.parent / "assets"

st.set_page_config(layout='wide')

SideBarLinks()

st.write("# About this App")

st.markdown(
    """
    Lobbying is when organizations, corporations, nonprofits, trade groups, and more,
    try to influence government policy by meeting with politicians and officials, funding
    campaigns, and advocating for their interests. In the EU, this happens on a massive
    scale, with thousands of organizations spending hundreds of millions of euros every
    year to shape legislation that affects all of us.

    The problem is that while this data is technically public, it's scattered across
    different databases, hard to search, and nearly impossible to make sense of without
    spending hours digging through spreadsheets. Most people have no idea who is lobbying
    on the policies that directly affect their lives.

    We built LobbyLens, a web app that combines lobbying data from LobbyFacts.eu with
    World Bank economic indicators to make EU lobbying transparent and accessible.
    Whether you're a journalist following the money, a researcher studying political
    influence, or a citizen who just wants to know who is shaping EU policy, LobbyLens
    gives you the tools to find out.
    """
)

st.markdown("---")
st.write("## Our Team")

authors = [
    {
        "name": "Alyssa D.",
        "role": "CS · Frontend & Data Modeling",
        "image": "Alyssa_Headshot.jpeg",
        "bio": "Hi, I am Alyssa from Philadelphia, PA! I am a rising sophomore at Northeastern University, currently majoring in Business Finance and studying Data Science. Throughout this web development, I was responsible for the ER diagrams, wireframes, and frontend pages.",
        "linkedin": "https://www.linkedin.com/in/alyssa-diwale-571599283",
    },
    {
        "name": "Manav",
        "role": "CS · Backend & Database",
        "image": "Manav_Headshot.png",
        "bio": "Hi, I'm Manav, a rising second year at Northeastern University. For LobbyLens, I worked on the CS side of the project — including building the SQL DDL, database schema, and Flask REST API routes. Focused on data integrity and connecting the backend to the frontend.",
        "linkedin": "https://www.linkedin.com/in/manavmahida/",
    },
    {
        "name": "Mihika",
        "role": "DS · Machine Learning",
        "image": "Mihika_Headshot.jpeg",
        "bio": "Hi! I'm Mihika, a rising second-year Computing and Law student at Northeastern. For LobbyLens, I worked on the data science side of the project — including data cleaning and pipeline, feature engineering, building and fine-tuning both ML models, and improving the prediction UI with an interactive scatter plot and organization comparison flow.",
        "linkedin": "https://www.linkedin.com/in/mihika-mehta-1398852a4",
    },
    {
        "name": "Rishi",
        "role": "DS · Data & Visualization",
        "image": "Rishi_Headshot.jpeg",
        "bio": "Hi! I'm Rishi, a rising second year at Northeastern University. For LobbyLens, I worked on the data science side of the project — including data sourcing from LobbyFacts and the World Bank API, exploratory data analysis, building the data visualizations used throughout the app, and developing ML 2 which predicts whether a European political party is represented in parliament based on ideology scores and connects to the lobbying theme through the Integrity Watch MEP meetings dataset.",
        "linkedin": "https://www.linkedin.com/in/rishi-ponnapalli-8943082a9",
    },
]

for author in authors:
    col_img, col_text = st.columns([1, 3])

    with col_img:
        try:
            img = Image.open(STATIC / author["image"])
            w, h = img.size
            side = min(w, h)
            img = img.crop(((w-side)//2, (h-side)//2, (w+side)//2, (h+side)//2))
            st.image(img, width=180)
        except:
            st.write("📷")

    with col_text:
        st.markdown(f"### {author['name']}")
        st.markdown(author["bio"])
        if author["linkedin"]:
            st.link_button("LinkedIn", author["linkedin"])

    st.markdown("---")

if st.button("Return to Home", type="primary"):
    st.switch_page("Home.py")