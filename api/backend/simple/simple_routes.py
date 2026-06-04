from flask import Blueprint, jsonify, current_app, redirect, request, url_for
from backend.simple.playlist import sample_playlist_data
from backend.ml_models import lobby_model, model01, model02

# This blueprint handles basic routes useful for testing and demonstration
simple_routes = Blueprint("simple_routes", __name__)


# ------------------------------------------------------------
# / is the most basic route
# Once the api container is started, in a browser, go to
# localhost:4000/
@simple_routes.route("/")
def welcome():
    current_app.logger.info("GET / handler")
    return "<h1>Welcome to the Summer 2026 DoC Project Template REST API</h1>", 200


# ------------------------------------------------------------
# /playlist returns the sample playlist data contained in playlist.py
# (imported above)
@simple_routes.route("/playlist")
def get_playlist_data():
    current_app.logger.info("GET /playlist handler")
    return jsonify(sample_playlist_data), 200


# ------------------------------------------------------------
@simple_routes.route("/niceMessage", methods=["GET"])
def affirmation():
    current_app.logger.info("GET /niceMessage")
    message = """
    <h1>Think about it...</h1>
    <br />
    You only need to be 1% better today than you were yesterday!
    """
    return message, 200


# ------------------------------------------------------------
# Demonstrates how to redirect from one route to another.
# url_for() takes the blueprint name + function name as a string.
@simple_routes.route("/message")
def message():
    return redirect(url_for("simple_routes.affirmation"))


@simple_routes.route("/data")
def get_data():
    current_app.logger.info("GET /data handler")
    data = {"a": {"b": "123", "c": "Help"}, "z": {"b": "456", "c": "me"}}
    return jsonify(data), 200


# ------------------------------------------------------------
# model01 prediction route (not quite as nice as model02, but a basic demo)
@simple_routes.route("/prediction/<var_01>/<var_02>", methods=["GET"])
def get_prediction(var_01, var_02):
    current_app.logger.info("GET /prediction handler")

    try:
        prediction = model01.predict(var_01, var_02)
        current_app.logger.info(f"prediction value returned is {prediction}")
        return jsonify({
            "prediction": prediction,
            "input_variables": {"var01": var_01, "var02": var_02},
        }), 200

    except Exception as e:
        current_app.logger.error(f"Prediction error: {e}")
        return jsonify({"error": "Error processing prediction request"}), 500

# ------------------------------------------------------------
# model02 — single prediction
# URL:  GET /model2/prediction/<fossil_fuels>/<co2_upop>
# e.g.  /model2/prediction/74.5/0.0105
#
# Returns the predicted Belgium GDP per capita given the two inputs.
# The route passes raw strings to model02.predict(), which handles
# scaling, float conversion and raises ValueError on bad input.
# ------------------------------------------------------------
@simple_routes.route("/model2/prediction/<fossil_fuels>/<co2_upop>", methods=["GET"])
def get_model2_prediction(fossil_fuels, co2_upop):
    current_app.logger.info("GET /model2/prediction handler")
    try:
        prediction = model02.predict(fossil_fuels, co2_upop)
        current_app.logger.info(f"model02 prediction: {prediction:.2f}")
        return jsonify({
            "prediction":      round(prediction, 2),
            "input_variables": {
                "Fossil_Fuels": float(fossil_fuels),
                "CO2_Upop":     float(co2_upop),
            },
        }), 200
    except ValueError as e:
        current_app.logger.error(f"model02 input error: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"model02 prediction error: {e}")
        return jsonify({"error": "Error processing prediction request"}), 500


# ------------------------------------------------------------
# model02 — full observation set with predictions
# URL:  GET /model2/observations
#
# Returns the complete Belgium dataset (all 26 years) with a
# model-predicted GDP column added.  Used by the scatter plot
# on the admin ML page (22_Prettier_ML.py).
# ------------------------------------------------------------
@simple_routes.route("/model2/observations", methods=["GET"])
def get_model2_observations():
    current_app.logger.info("GET /model2/observations handler")
    try:
        data = model02.get_observations_with_predictions()
        current_app.logger.info(f"Returning {len(data)} observation rows")
        return jsonify(data), 200
    except Exception as e:
        current_app.logger.error(f"model02 observations error: {e}")
        return jsonify({"error": "Error fetching observations"}), 500


# ------------------------------------------------------------
# lobby_model — full prediction endpoint
# URL:  POST /lobby/prediction
#
# Accepts JSON payload with lobbying_cost, ep_passes, members_fte,
# country, and interest, then returns the model prediction.
# ------------------------------------------------------------
@simple_routes.route("/lobby/prediction", methods=["POST"])
def get_lobby_prediction():
    current_app.logger.info("POST /lobby/prediction handler")
    try:
        data = request.get_json(silent=True) or {}

        required_fields = ["lobbying_cost", "ep_passes", "members_fte", "country", "interest"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

        prediction = lobby_model.predict(
            data["lobbying_cost"],
            data["ep_passes"],
            data["members_fte"],
            data["country"],
            data["interest"],
        )

        current_app.logger.info(f"lobby prediction returned {prediction:.2f}")
        return jsonify({
            "prediction": round(prediction, 2),
            "input_variables": {
                "lobbying_cost": float(data["lobbying_cost"]),
                "ep_passes": float(data["ep_passes"]),
                "members_fte": float(data["members_fte"]),
                "country": data["country"],
                "interest": data["interest"],
            },
        }), 200

    except ValueError as e:
        current_app.logger.error(f"lobby prediction input error: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"lobby prediction error: {e}")
        return jsonify({"error": "Error processing prediction request"}), 500
