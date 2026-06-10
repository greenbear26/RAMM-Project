"""
model01.py demonstrates how to store model parameters in the database
and retrieve them at prediction time via a REST route.
"""
import json
import numpy as np
from flask import current_app
from backend.db_connection import get_db

country_to_iso2 = {
    'Austria': 'AUT',
    'Belgium': 'BEL',
    'Bulgaria': 'BGR',
    'Croatia': 'HRV',
    'Cyprus': 'CYP',
    'Czech Republic': 'CYP',
    'Denmark': 'DNK',
    'Estonia': 'EST',
    'Finland': 'FIN',
    'France': 'FRA',
    'Germany': 'DEU',
    'Greece': 'GRC',
    'Hungary': 'HUN',
    'Ireland': 'IRL',
    'Italy': 'ITA',
    'Latvia': 'LVA',
    'Lithuania': 'LTU',
    'Luxembourg': 'LUX',
    'Malta': 'MLT',
    'Netherlands': 'NLD',
    'Poland': 'POL',
    'Portugal': 'PRT',
    'Romania': 'ROU',
    'Slovenia': 'SVN',
    'Spain': 'ESP',
    'Sweden': 	'SWE'
}

def _get_country_data(country):
    """
    Retrieves country-specific data from the database for use in predictions.

    Args:
        country (str): The name of the country to retrieve data for.

    Returns:
        dict: A dictionary containing country-specific data such as GDP, population, and inflation.
    """
    iso2 = country_to_iso2.get(country)
    if iso2 is None:
        raise ValueError(f"Country '{country}' not found in mapping")
    
    with get_db().cursor(dictionary=True) as cursor:
        query = 'SELECT gdp_usd, population, inflation FROM country_indicator WHERE country_code = %s'
        cursor.execute(query, (iso2,))
        row = cursor.fetchone()

    return row

# ------------------------------------------------------------
# Internal helpers — fetch the latest beta vector from the DB.
# Also fetch the scaler parameters that are stored in the DB.
# Kept private (leading underscore) so routes import the public
# functions below rather than the raw DB call.
# ------------------------------------------------------------
def _get_params():
    """
    Fetches the most recent parameter vector from lobby_model_weights.

    Returns:
        np.ndarray: 1-D array [intercept, b_Fossil_Fuels, b_CO2_Upop]

    Raises:
        ValueError: if no parameters exist in the database yet.
    """
    with get_db().cursor(dictionary=True) as cursor:
        cursor.execute(
            'SELECT beta_vals FROM lobby_model_weights ORDER BY model_id DESC LIMIT 1'
        )
        row = cursor.fetchone()

    if row is None:
        raise ValueError("No model2 parameters found in the database.")

    # beta_vals is stored as a JSON-style list string e.g. "[1.2, 3.4, 5.6]"
    params = np.array(json.loads(row['beta_vals']))
    current_app.logger.info(f'model02 params loaded: {params}')
    return params

def _get_scaler_params():
    with get_db().cursor(dictionary=True) as cursor:
        cursor.execute(
            'SELECT feature_means, feature_stds FROM lobby_model_scaler '
            'ORDER BY sequence_number DESC LIMIT 1'
        )
        row = cursor.fetchone()
    if row is None:
        raise ValueError("No model2 scaler parameters found in the database.")
    means = np.array(json.loads(row['feature_means']))
    stds  = np.array(json.loads(row['feature_stds']))
    return means, stds

def predict(lobbying_cost, ep_passes, members_fte, country, interest):
    """
    Retrieves model parameters from the database and uses them for
    real-time prediction. Parameters are stored as a comma-separated
    string and parsed into a numpy array here.

    Raises ValueError if inputs cannot be converted to float, or if
    no model parameters exist in the database yet.

    Args:
        lobbying_cost (str): The lobbying cost input as a string.
        ep_passes (str): The number of EP passes input as a string.
        members_fte (str): The number of full time employess input as a string.
        country (str): The country input as a string.
        interest (str): The interest input as a string.
    """
    # Input validation belongs here at the boundary between the route and the model.
    # If conversion fails, ValueError propagates up to the route handler.
    log_lobbying_cost = np.log(float(lobbying_cost))
    log_ep_passes = np.log(float(ep_passes))

    # Get country dataset using route
    country_data = _get_country_data(country)
    if country_data is None:
        raise ValueError(f"No country data found for '{country}'")

    # lobbying_to_gdp_ratio = float(lobbying_cost) / country_data['gdp_usd']
    members = float(members_fte)
    members_squared = members ** 2

    interest_0 = 0
    interest_1 = 0
    if (interest == 'Does not represent commercial interests'):
        interest_0 = 1
    elif (interest == 'Promotes their own interests or the collective interests of their members'):
        interest_1 = 1

    params = _get_params()
    means, stds = _get_scaler_params()

    # apply the same standardization used at training time
    x_scaled = (np.array([log_lobbying_cost, log_ep_passes, members, members_squared, 
                          interest_0, interest_1]) - means) / stds
    
    # [1, x1, x2] . [intercept, b1, b2]
    input_vec = np.array([1.0, x_scaled[0], x_scaled[1], x_scaled[2], x_scaled[3], x_scaled[4], x_scaled[5]])
    prediction = float(params.T @ input_vec)
    actual_prediction = np.exp(prediction)  # reverse the log transformation to get back to original scale
    current_app.logger.info(
        f"lobby_model.predict({lobbying_cost}, {ep_passes}, {members_fte}, {country}, {interest}) -> {actual_prediction:.2f}"
    )
    return actual_prediction
