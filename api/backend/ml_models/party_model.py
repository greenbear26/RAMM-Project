"""
model01.py demonstrates how to store model parameters in the database
and retrieve them at prediction time via a REST route.
"""
import json
import numpy as np
from flask import current_app
from backend.db_connection import get_db

country_to_index = {
    "Belgium": 0,
    "Bulgaria": 1,
    "Croatia": 2,
    "Cyprus": 3,
    "Czech Republic": 4,
    "Denmark": 5,
    "Estonia": 6,
    "Finland": 7,
    "France": 8,
    "Germany": 9,
    "Greece": 10,
    "Hungary": 11,
    "Ireland": 12,
    "Italy": 13,
    "Latvia": 14,
    "Lithuania": 15,
    "Luxembourg": 16,
    "Malta": 17,
    "Netherlands": 18,
    "Poland": 19,
    "Portugal": 20,
    "Romania": 21,
    "Slovenia": 22,
    "Spain": 23,
    "Sweden": 24,
}

# ------------------------------------------------------------
# Internal helpers — fetch the latest beta vector from the DB.
# Also fetch the scaler parameters that are stored in the DB.
# Kept private (leading underscore) so routes import the public
# functions below rather than the raw DB call.
# ------------------------------------------------------------
def _get_params():
    """
    Fetches the most recent parameter vector from party_model_weights.

    Returns:
        np.ndarray: 1-D array

    Raises:
        ValueError: if no parameters exist in the database yet.
    """
    with get_db().cursor(dictionary=True) as cursor:
        cursor.execute(
            'SELECT beta_vals FROM party_model_weights ORDER BY model_id DESC LIMIT 1'
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
            'SELECT feature_means, feature_stds FROM party_model_scaler '
            'ORDER BY sequence_number DESC LIMIT 1'
        )
        row = cursor.fetchone()
    if row is None:
        raise ValueError("No model2 scaler parameters found in the database.")
    means = np.array(json.loads(row['feature_means']))
    stds  = np.array(json.loads(row['feature_stds']))
    return means, stds

def predict(populist, populist_bl, farright, farright_bl, farleft, farleft_bl, 
            eurosceptic, eurosceptic_bl, country_name, eu_anti_pro):
    """
    Retrieves model parameters from the database and uses them for
    real-time prediction. Parameters are stored as a comma-separated
    string and parsed into a numpy array here.

    Raises ValueError if inputs cannot be converted to float, or if
    no model parameters exist in the database yet.

    Args:
        populist (int): 0 or 1, if the party is populist
        populist_bl (int): 0 or 1, if the party is populist borderline
        farright (int): 0 or 1, if the party is far right
        farright_bl (int): 0 or 1, if the party is far right borderline
        farleft (int): 0 or 1, if the party is far left
        farleft_bl (int): 0 or 1, if the party is far left borderline
        eurosceptic (int): 0 or 1, if the party is eurosceptic
        eurosceptic_bl (int): 0 or 1, if the party is eurosceptic borderline
        country_name (str): name of the country (e.g "Germany", "France", etc.)
        eu_anti_pro (float): numeric score of how pro-EU the party is, from 0 to 10
    """
    X = [int(populist), int(populist_bl), int(farright), int(farright_bl),
         int(farleft), int(farleft_bl), int(eurosceptic), int(eurosceptic_bl), 
         float(eu_anti_pro), float(eu_anti_pro) ** 2]
    
    # One-hot encode country_name
    country_index = country_to_index.get(country_name)
    if country_index is None and country_name != "Austria":
        raise ValueError(f"Invalid country name: {country_name}")
    country_dummies = [0] * len(country_to_index)
    if country_index is not None:
        country_dummies[country_index] = 1

    X += country_dummies

    params = _get_params()
    means, stds = _get_scaler_params()

    # apply the same standardization used at training time
    x_scaled = (np.array(X) - means) / stds
    
    # Apply logistic function to the linear combination of inputs and parameters
    linear_combination = np.dot(params, np.array([1.0] + list(x_scaled)))  # add intercept term
    prediction = 1 / (1 + np.exp(-linear_combination))
    return prediction
