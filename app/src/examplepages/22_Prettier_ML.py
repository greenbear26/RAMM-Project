import logging
logger = logging.getLogger(__name__)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests

from modules.nav import SideBarLinks

st.set_page_config(layout='wide')
SideBarLinks()

st.title('Belgium GDP Model — Interactive Demo')
st.write("""
Moving Jupyter notebook models to Streamlit -> 
The model parameters are stored in the DB and fetched at prediction time.
The user inputs raw values via sliders, the function auto scales and then predicts.

**Model**: GDP per capita (EUR) ~ Fossil Fuels (%) + CO₂ / Urban Population  
**Data**: Belgium, 1990–2015 (World Bank)
""")

st.divider()

# ============================================================
# Section 1: Single Prediction
# ============================================================
st.header('Make a Prediction')
st.write(
    "Enter values for the two predictors below. "
    "Typical Belgium ranges are shown as slider defaults."
)

col1, col2 = st.columns(2)

with col1:
    fossil_fuels = st.slider(
        label='Fossil Fuels (% of total energy)',
        min_value=60.0,
        max_value=85.0,
        value=74.0,
        step=0.1,
        format="%.1f",
        help="Fossil fuel energy consumption as a percentage of total energy use."
    )

with col2:
    co2_upop = st.slider(
        label='CO₂ / Urban Population  (kt per person)',
        min_value=0.007,
        max_value=0.014,
        value=0.0105,
        step=0.0001,
        format="%.4f",
        help="CO₂ emissions (kt) divided by urban population — a per-capita emissions intensity measure."
    )

if st.button('Calculate Predicted GDP', type='primary', use_container_width=True):
    logger.info(f'Prediction request: Fossil_Fuels={fossil_fuels}, CO2_Upop={co2_upop}')
    try:
        response = requests.get(
            f'http://web-api:4000/model2/prediction/{fossil_fuels}/{co2_upop}'
        )
        response.raise_for_status()
        result = response.json()

        pred = result['prediction']

        # Display the result with st.metric for a clean look
        st.success('Prediction complete!')
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric(label='CO₂/Urban Pop Input', value=f'{co2_upop:.4f}')
        with m2:
            st.metric(label='Fossil Fuels Input', value=f'{fossil_fuels:.1f}%')
        with m3:
            st.metric(label='Predicted GDP per Capita', value=f'€{pred:,.0f}')

        # Interpretation note
        st.info(
            f"The model predicts a Belgium GDP per capita of **€{pred:,.0f}** "
            f"when fossil fuel consumption is **{fossil_fuels:.1f}%** of total energy "
            f"and CO₂ per urban resident is **{co2_upop:.4f} kt/person**."
        )

    except Exception as e:
        logger.error(f'Prediction error: {e}')
        st.error(f'Could not retrieve prediction: {e}')

st.divider()

# ============================================================
# Section 2: Observed vs Predicted Plot
# ============================================================
st.header('Observed vs. Predicted GDP (1990–2015)')
st.write(
    "The plot below shows the model's fit to the full Belgium dataset. "
    "Points close to the diagonal dashed line indicate accurate predictions. "
    "Hover over any point to see the year and inputs."
)

try:
    obs_response = requests.get('http://web-api:4000/model2/observations')
    obs_response.raise_for_status()
    obs_data = obs_response.json()
    df = pd.DataFrame(obs_data)

    # ---- Observed vs Predicted scatter ----
    fig = px.scatter(
        df,
        x='GDP',
        y='GDP_predicted',
        hover_name='year',
        hover_data={
            'GDP':           ':.0f',
            'GDP_predicted': ':.0f',
            'Fossil_Fuels':  ':.2f',
            'CO2_Upop':      ':.5f',
        },
        labels={
            'GDP':           'Observed GDP per Capita (€)',
            'GDP_predicted': 'Predicted GDP per Capita (€)',
        },
        title='Observed vs. Predicted Belgium GDP per Capita',
        ## Optionally: color points by residual to show where the model over/under-predicts (or some other feature)
        # color='residual',
        # color_continuous_scale='RdBu',
        # color_continuous_midpoint=0,
    )

    # Add perfect-fit diagonal
    min_val = min(df['GDP'].min(), df['GDP_predicted'].min()) * 0.95
    max_val = max(df['GDP'].max(), df['GDP_predicted'].max()) * 1.05
    fig.add_trace(
        go.Scatter(
            x=[min_val, max_val],
            y=[min_val, max_val],
            mode='lines',
            line=dict(color='red', dash='dash', width=1),
            name='Perfect fit',
            showlegend=True,
        )
    )

    ## Optional: add residuals as hover data or color points by residual to show where the model over/under-predicts
    # fig.update_layout(
    #     height=520,
    #     coloraxis_colorbar=dict(title='Residual (€)'),
    # )
    st.plotly_chart(fig, use_container_width=True)

    # ---- GDP over time: observed and predicted ----
    st.write("#### GDP Over Time: Observed vs. Predicted")
    fig2 = px.line(
        df,
        x='year',
        y=['GDP', 'GDP_predicted'],
        labels={'value': 'GDP per Capita (€)', 'year': 'Year', 'variable': 'Series'},
        title='Belgium GDP per Capita: Observed and Model Fit (1990–2015)',
        hover_data={'Fossil_Fuels': ':.2f', 'CO2_Upop': ':.5f'},
    )
    fig2.update_traces(mode='lines+markers')
    fig2.update_layout(height=400, legend_title_text='')
    st.plotly_chart(fig2, use_container_width=True)

    # ---- Summary stats table ----
    st.write("#### Model Summary")
    residuals = df['residual']
    rmse = np.sqrt((residuals**2).mean())
    r2   = 1 - (residuals**2).sum() / ((df['GDP'] - df['GDP'].mean())**2).sum()

    s1, s2, s3 = st.columns(3)
    s1.metric('R²  (in-sample)', f'{r2:.3f}')
    s2.metric('RMSE', f'€{rmse:,.0f}')
    s3.metric('Observations', len(df))

    with st.expander('Show raw data table'):
        st.dataframe(
            df.rename(columns={
                'year':          'Year',
                'GDP':           'Observed GDP (€)',
                'GDP_predicted': 'Predicted GDP (€)',
                'residual':      'Residual (€)',
                'Fossil_Fuels':  'Fossil Fuels (%)',
                'CO2_Upop':      'CO₂/Urban Pop',
            }),
            use_container_width=True,
            hide_index=True,
        )

except Exception as e:
    logger.error(f'Observations fetch error: {e}')
    st.error(f'Could not load observation data: {e}')
