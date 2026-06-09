import logging
logger = logging.getLogger(__name__)

from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from backend.utils import error_response
from mysql.connector import Error
from ml_models.lobby_model import predict as lobby_predict
from ml_models.party_model import predict as party_predict

organizations_bp = Blueprint("organizations", __name__)
countries_bp     = Blueprint("countries", __name__)
users_bp         = Blueprint("users", __name__)
ml_bp            = Blueprint("ml", __name__)


# test route:
@organizations_bp.route("/test", methods=["GET"])
def test_route():
    current_app.logger.info("GET /test")
    query = "select country from country_indicator;"
    with get_db().cursor(dictionary=True) as cursor:
        cursor.execute(query)
        countries = cursor.fetchall()
    return jsonify(countries), 200

# Route 1 — GET /organizations
# Search / filter all organizations by policy area, country, or industry.
@organizations_bp.route("/organizations", methods=["GET"])
def get_all_organizations():
    current_app.logger.info("GET /organizations")
    try:
        country   = request.args.get("country")       # e.g. "Belgium"
        interest  = request.args.get("interest")      # e.g. "commercial"
        min_cost  = request.args.get("min_cost")      # e.g. "1000000"
        max_cost  = request.args.get("max_cost")
        limit     = int(request.args.get("limit", 50))

        # country_code stores full names (e.g. "Belgium") from Head office column
        query  = """
            SELECT org_id, name, members_fte, lobbying_cost,
                   interest_represented, country_code, eu_office,
                   ep_passes_current, ep_passes_all, meetings
            FROM organization
            WHERE 1=1
        """
        params = []

        if country:
            query += " AND country_code = %s"
            params.append(country)
        if interest:
            query += " AND interest_represented LIKE %s"
            params.append(f"%{interest}%")
        if min_cost:
            query += " AND lobbying_cost >= %s"
            params.append(float(min_cost))
        if max_cost:
            query += " AND lobbying_cost <= %s"
            params.append(float(max_cost))

        query += " ORDER BY lobbying_cost DESC LIMIT %s"
        params.append(limit)

        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute(query, params)
            orgs = cursor.fetchall()

        current_app.logger.info(f"Retrieved {len(orgs)} organizations")
        return jsonify(orgs), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_all_organizations: {e}")
        return error_response(str(e))


# ROUTE 2 — GET /organizations/<org_id>
# Full org profile — name, spend, meetings, EP passes, activities.
@organizations_bp.route("/organizations/<int:org_id>", methods=["GET"])
def get_organization(org_id):
    current_app.logger.info(f"GET /organizations/{org_id}")
    try:
        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute(
                """SELECT org_id, name, members_fte, lobbying_cost,
                          interest_represented, country_code, eu_office,
                          ep_passes_current, ep_passes_all, meetings
                   FROM organization WHERE org_id = %s""",
                (org_id,)
            )
            org = cursor.fetchone()
            if not org:
                return error_response("Organization not found", 404)

            # Attach expenditure history
            cursor.execute(
                "SELECT year, amount_eur FROM expenditure_record WHERE org_id = %s ORDER BY year DESC",
                (org_id,)
            )
            org["expenditures"] = cursor.fetchall()

            # Attach lobbying activities
            cursor.execute(
                """SELECT la.activity_type, la.eu_institution, la.start_date,
                          pa.name AS policy_area
                   FROM lobbying_activity la
                   LEFT JOIN policy_area pa ON la.policy_area_id = pa.policy_area_id
                   WHERE la.org_id = %s""",
                (org_id,)
            )
            org["lobbying_activities"] = cursor.fetchall()

        return jsonify(org), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_organization: {e}")
        return error_response(str(e))


# Route 3 — POST /organizations
# Add a new organization.
@organizations_bp.route("/organizations", methods=["POST"])
def create_organization():
    current_app.logger.info("POST /organizations")
    try:
        data = request.get_json()

        required_fields = ["name", "country_code", "lobbying_cost"]
        for field in required_fields:
            if field not in data:
                return error_response(f"Missing required field: {field}", 400)

        query = """
            INSERT INTO organization
                (name, members_fte, lobbying_cost, interest_represented,
                 country_code, eu_office, ep_passes_current, ep_passes_all, meetings)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute(query, (
                data["name"],
                data.get("members_fte"),
                data["lobbying_cost"],
                data.get("interest_represented"),
                data["country_code"],
                data.get("eu_office"),
                data.get("ep_passes_current"),
                data.get("ep_passes_all"),
                data.get("meetings"),
            ))
            new_id = cursor.lastrowid

        get_db().commit()
        current_app.logger.info(f"Created organization id={new_id}")
        return jsonify({"message": "Organization created successfully", "org_id": new_id}), 201
    except Error as e:
        current_app.logger.error(f"Database error in create_organization: {e}")
        return error_response(str(e))


# Route 4 — PUT /organizations/<org_id>
# Update any fields on an existing organization.
@organizations_bp.route("/organizations/<int:org_id>", methods=["PUT"])
def update_organization(org_id):
    current_app.logger.info(f"PUT /organizations/{org_id}")
    try:
        data = request.get_json()

        allowed_fields = [
            "name", "members_fte", "lobbying_cost", "interest_represented",
            "country_code", "eu_office", "ep_passes_current", "ep_passes_all", "meetings"
        ]
        update_fields = [f"{f} = %s" for f in allowed_fields if f in data]
        params        = [data[f] for f in allowed_fields if f in data]

        if not update_fields:
            return error_response("No valid fields to update", 400)

        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute("SELECT org_id FROM organization WHERE org_id = %s", (org_id,))
            if not cursor.fetchone():
                return error_response("Organization not found", 404)

            params.append(org_id)
            cursor.execute(
                f"UPDATE organization SET {', '.join(update_fields)} WHERE org_id = %s",
                params
            )

        get_db().commit()
        return jsonify({"message": "Organization updated successfully"}), 200
    except Error as e:
        current_app.logger.error(f"Database error in update_organization: {e}")
        return error_response(str(e))


# ROUTE 5 — DELETE /organizations/<org_id>
# Remove an organization from the database.
@organizations_bp.route("/organizations/<int:org_id>", methods=["DELETE"])
def delete_organization(org_id):
    current_app.logger.info(f"DELETE /organizations/{org_id}")
    try:
        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute("SELECT org_id FROM organization WHERE org_id = %s", (org_id,))
            if not cursor.fetchone():
                return error_response("Organization not found", 404)
            cursor.execute("DELETE FROM organization WHERE org_id = %s", (org_id,))

        get_db().commit()
        current_app.logger.info(f"Deleted organization id={org_id}")
        return jsonify({"message": "Organization deleted successfully"}), 200
    except Error as e:
        current_app.logger.error(f"Database error in delete_organization: {e}")
        return error_response(str(e))



# Route 6 — GET /policy-areas
# Fetch all policy areas to populate the search dropdown.
@organizations_bp.route("/policy-areas", methods=["GET"])
def get_policy_areas():
    current_app.logger.info("GET /policy-areas")
    try:
        country = request.args.get("country")
        limit   = int(request.args.get("limit", 10))

        query  = """
            SELECT org_id, name, lobbying_cost, country_code,
                   interest_represented, meetings, ep_passes_all
            FROM organization
            WHERE lobbying_cost IS NOT NULL
        """
        params = []
        if country:
            query += " AND country_code = %s"
            params.append(country)

        query += " ORDER BY lobbying_cost DESC LIMIT %s"
        params.append(limit)

        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute(query, params)
            orgs = cursor.fetchall()

        return jsonify(orgs), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_top_spenders: {e}")
        return error_response(str(e))



# Route 7 — GET /country-indicators/<country_code>
# Fetch GDP, population, and inflation for a given country (Clouseau detail cards).
@countries_bp.route("/country-indicators/<string:country_code>", methods=["GET"])
def get_country_indicators(country_code):
    current_app.logger.info(f"GET /country-indicators/{country_code}")
    try:
        with get_db().cursor(dictionary=True) as cursor:
            # country_code stores full names (e.g. "Belgium") from GDP data
            cursor.execute(
                "SELECT * FROM country WHERE country_code = %s", (country_name,)
            )
            country = cursor.fetchone()
            if not country:
                return error_response(f"Country '{country_name}' not found", 404)

            # GDP_Energy_WBdat: year, gdp_usd, fossil_fuels, co2_emit, urban_pop
            cursor.execute(
                """SELECT year, gdp_usd, fossil_fuels, co2_emit, urban_pop
                   FROM country_indicator
                   WHERE country_code = %s
                   ORDER BY year DESC""",
                (country_name,)
            )
            country["indicators"] = cursor.fetchall()

            # Also return how many orgs are headquartered here
            cursor.execute(
                """SELECT COUNT(*) AS org_count,
                          SUM(lobbying_cost) AS total_lobbying_spend
                   FROM organization WHERE country_code = %s""",
                (country_name,)
            )
            country["lobbying_summary"] = cursor.fetchone()

        return jsonify(country), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_country_indicators: {e}")
        return error_response(str(e))


# Route 8 — GET /preferences
# Get the current user's saved policy + country preferences (Stromae feed).
@users_bp.route("/preferences", methods=["GET"])
def get_preferences():
    current_app.logger.info("GET /preferences")
    try:
        user_id = request.args.get("user_id")
        if not user_id:
            return error_response("Missing required parameter: user_id", 400)

        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT user_id, email, role FROM app_user WHERE user_id = %s",
                (user_id,)
            )
            user = cursor.fetchone()
            if not user:
                return error_response("User not found", 404)

            cursor.execute(
                """SELECT export_id, query_json, file_format, created_at
                   FROM saved_query_export
                   WHERE user_id = %s ORDER BY created_at DESC""",
                (user_id,)
            )
            user["saved_queries"] = cursor.fetchall()

        return jsonify(user), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_preferences: {e}")
        return error_response(str(e))


# Route 9 — POST /preferences
# Submit onboarding preferences — policy areas & countries (Stromae onboarding).
@users_bp.route("/preferences", methods=["POST"])
def save_preferences():
    current_app.logger.info("POST /preferences")
    try:
        data = request.get_json()

        for field in ["user_id", "query_json"]:
            if field not in data:
                return error_response(f"Missing required field: {field}", 400)

        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT user_id FROM app_user WHERE user_id = %s", (data["user_id"],)
            )
            if not cursor.fetchone():
                return error_response("User not found", 404)

            cursor.execute(
                """INSERT INTO saved_query_export (user_id, query_json, file_format)
                   VALUES (%s, %s, %s)""",
                (data["user_id"], data["query_json"], data.get("file_format", "json"))
            )
            new_id = cursor.lastrowid

        get_db().commit()
        current_app.logger.info(f"Saved preferences export_id={new_id}")
        return jsonify({"message": "Preferences saved successfully", "export_id": new_id}), 201
    except Error as e:
        current_app.logger.error(f"Database error in save_preferences: {e}")
        return error_response(str(e))



# Route 10 — POST /lobby/prediction
# Submit lobbying inputs and return the model prediction.
@ml_bp.route("/lobby/prediction", methods=["POST"])
def get_lobby_prediction():
    current_app.logger.info("POST /lobby/prediction")
    try:
        data = request.get_json(silent=True) or {}

        required_fields = ["lobbying_cost", "ep_passes", "members_fte", "country", "interest"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

        prediction = lobby_predict(
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

@ml_bp.route("/party/prediction", methods=["POST"])
def get_party_prediction():
    current_app.logger.info("POST /party/prediction")
    try:
        data = request.get_json(silent=True) or {}

        required_fields = [
            "populist", "populist_bl", "farright", "farright_bl", "farleft", "farleft_bl",
            "eurosceptic", "eurosceptic_bl", "country_name", "eu_anti_pro"
        ]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

        prediction = party_predict(
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
                "populist": int(data["populist"]),
                "populist_bl": int(data["populist_bl"]),
                "farright": int(data["farright"]),
                "farright_bl": int(data["farright_bl"]),
                "farleft": int(data["farleft"]),
                "farleft_bl": int(data["farleft_bl"]),
                "eurosceptic": int(data["eurosceptic"]),
                "eurosceptic_bl": int(data["eurosceptic_bl"]),
                "country_name": data["country_name"],
                "eu_anti_pro": float(data["eu_anti_pro"]),
            },
        }), 200

    except ValueError as e:
        current_app.logger.error(f"party prediction input error: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"party prediction error: {e}")
        return jsonify({"error": "Error processing prediction request"}), 500

def main():
    print(test_route())
if __name__ == "__main__":
    main()