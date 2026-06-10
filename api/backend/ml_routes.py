import logging
logger = logging.getLogger(__name__)

from flask import Blueprint, jsonify, request, current_app
from backend.ml_models import lobby_model
from backend.ml_models import party_model

ml_bp = Blueprint("ml", __name__)


# Route 10 — POST /lobby/prediction
@ml_bp.route("/lobby/prediction", methods=["POST"])
def get_lobby_prediction():
    current_app.logger.info("POST /lobby/prediction")
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
                "ep_passes":     float(data["ep_passes"]),
                "members_fte":   float(data["members_fte"]),
                "country":       data["country"],
                "interest":      data["interest"],
            },
        }), 200
    except ValueError as e:
        current_app.logger.error(f"lobby prediction input error: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"lobby prediction error: {e}")
        return jsonify({"error": "Error processing prediction request"}), 500


# Route 11 — POST /party/prediction
@ml_bp.route("/party/prediction", methods=["POST"])
def get_party_prediction():
    current_app.logger.info("POST /party/prediction")
    try:
        data = request.get_json(silent=True) or {}

        required_fields = [
            "populist", "populist_bl", "farright", "farright_bl",
            "farleft", "farleft_bl", "eurosceptic", "eurosceptic_bl",
            "country_name", "eu_anti_pro"
        ]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

        prediction = party_model.predict(
            data["populist"],
            data["populist_bl"],
            data["farright"],
            data["farright_bl"],
            data["farleft"],
            data["farleft_bl"],
            data["eurosceptic"],
            data["eurosceptic_bl"],
            data["country_name"],
            data["eu_anti_pro"]
        )

        current_app.logger.info(f"party prediction returned {prediction:.2f}")
        return jsonify({
            "prediction": round(prediction, 2),
            "input_variables": {
                "populist":       int(data["populist"]),
                "populist_bl":    int(data["populist_bl"]),
                "farright":       int(data["farright"]),
                "farright_bl":    int(data["farright_bl"]),
                "farleft":        int(data["farleft"]),
                "farleft_bl":     int(data["farleft_bl"]),
                "eurosceptic":    int(data["eurosceptic"]),
                "eurosceptic_bl": int(data["eurosceptic_bl"]),
                "country_name":   data["country_name"],
                "eu_anti_pro":    float(data["eu_anti_pro"]),
            },
        }), 200
    except ValueError as e:
        current_app.logger.error(f"party prediction input error: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"party prediction error: {e}")
        return jsonify({"error": "Error processing prediction request"}), 500