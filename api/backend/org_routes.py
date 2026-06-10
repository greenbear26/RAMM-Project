import logging
logger = logging.getLogger(__name__)

from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from backend.utils import error_response
from backend.ml_models import lobby_model
from mysql.connector import Error

organizations_bp = Blueprint("organizations", __name__)


# Route 1 — GET /organizations
@organizations_bp.route("/organizations", methods=["GET"])
def get_all_organizations():
    current_app.logger.info("GET /organizations")
    try:
        country     = request.args.get("country")
        interest    = request.args.get("interest")
        policy_area = request.args.get("policy_area")
        min_cost    = request.args.get("min_cost")
        max_cost    = request.args.get("max_cost")
        name        = request.args.get("name")
        limit       = int(request.args.get("limit", 50))

        query = """
            SELECT DISTINCT o.org_id, o.name, o.members_eu, o.members_fte,
                   o.lobbying_cost, o.interest_represented, o.country_code,
                   o.industry_id, o.lobbyfacts_url
            FROM organization o
            LEFT JOIN lobbying_activity la ON o.org_id = la.org_id
            LEFT JOIN policy_area pa ON la.policy_area_id = pa.policy_area_id
            WHERE 1=1
        """
        params = []

        if country:
            query += " AND o.country_code = %s"
            params.append(country)
        if interest:
            query += " AND o.interest_represented LIKE %s"
            params.append(f"%{interest}%")
        if policy_area:
            query += " AND pa.name = %s"
            params.append(policy_area)
        if min_cost:
            query += " AND o.lobbying_cost >= %s"
            params.append(float(min_cost))
        if max_cost:
            query += " AND o.lobbying_cost <= %s"
            params.append(float(max_cost))
        if name:
            query += " AND o.name LIKE %s"
            params.append(f"%{name}%")

        query += " ORDER BY o.lobbying_cost DESC LIMIT %s"
        params.append(limit)

        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute(query, params)
            orgs = cursor.fetchall()

        current_app.logger.info(f"Retrieved {len(orgs)} organizations")
        return jsonify(orgs), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_all_organizations: {e}")
        return error_response(str(e))


# Route 2 — GET /organizations/summary
@organizations_bp.route("/organizations/summary", methods=["GET"])
def get_organizations_summary():
    current_app.logger.info("GET /organizations/summary")
    try:
        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*)                          AS total_orgs,
                    COALESCE(SUM(lobbying_cost), 0)   AS total_spend,
                    COALESCE(AVG(lobbying_cost), 0)   AS avg_spend,
                    COALESCE(MAX(lobbying_cost), 0)   AS max_spend,
                    COUNT(DISTINCT country_code)      AS countries_represented
                FROM organization
            """)
            summary = cursor.fetchone()

            cursor.execute("""
                SELECT country_code, COUNT(*) AS org_count
                FROM organization
                WHERE country_code IS NOT NULL
                GROUP BY country_code
                ORDER BY org_count DESC
                LIMIT 1
            """)
            top_country = cursor.fetchone()
            summary["top_country"] = top_country["country_code"] if top_country else None

        return jsonify(summary), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_organizations_summary: {e}")
        return error_response(str(e))


# Route 3 — GET /organizations/top
@organizations_bp.route("/organizations/top", methods=["GET"])
def get_top_organizations():
    current_app.logger.info("GET /organizations/top")
    try:
        limit = min(int(request.args.get("limit", 10)), 100)
        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT org_id, name, lobbying_cost, country_code, interest_represented
                FROM organization
                WHERE lobbying_cost IS NOT NULL
                ORDER BY lobbying_cost DESC
                LIMIT %s
            """, (limit,))
            orgs = cursor.fetchall()
        return jsonify(orgs), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_top_organizations: {e}")
        return error_response(str(e))


# Route 4 — GET /organizations/<org_id>
@organizations_bp.route("/organizations/<int:org_id>", methods=["GET"])
def get_organization(org_id):
    current_app.logger.info(f"GET /organizations/{org_id}")
    try:
        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute(
                """SELECT org_id, name, members_eu, members_fte, lobbying_cost,
                          interest_represented, country_code, industry_id, lobbyfacts_url
                   FROM organization WHERE org_id = %s""",
                (org_id,)
            )
            org = cursor.fetchone()
            if not org:
                return error_response("Organization not found", 404)

            cursor.execute(
                "SELECT expenditure_id, year, amount_eur FROM expenditure_record WHERE org_id = %s ORDER BY year DESC",
                (org_id,)
            )
            org["expenditures"] = cursor.fetchall()

            cursor.execute(
                """SELECT la.activity_id, la.activity_type, la.eu_institution, la.start_date,
                          pa.name AS policy_area
                   FROM lobbying_activity la
                   LEFT JOIN policy_area pa ON la.policy_area_id = pa.policy_area_id
                   WHERE la.org_id = %s""",
                (org_id,)
            )
            org["lobbying_activities"] = cursor.fetchall()

            cursor.execute(
                "SELECT COALESCE(SUM(attendees_count), 0) AS meeting_count FROM meeting WHERE org_id = %s",
                (org_id,)
            )
            org["meetings"] = cursor.fetchone()["meeting_count"]

        return jsonify(org), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_organization: {e}")
        return error_response(str(e))


# Route 5 — GET /organizations/<org_id>/influence-prediction
@organizations_bp.route("/organizations/<int:org_id>/influence-prediction", methods=["GET"])
def get_org_influence_prediction(org_id):
    current_app.logger.info(f"GET /organizations/{org_id}/influence-prediction")
    try:
        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute(
                """SELECT lobbying_cost, members_fte, country_code, interest_represented
                   FROM organization WHERE org_id = %s""",
                (org_id,)
            )
            org = cursor.fetchone()
            if not org:
                return error_response("Organization not found", 404)

            cursor.execute(
                "SELECT COUNT(*) AS ep_passes FROM access_pass WHERE org_id = %s",
                (org_id,)
            )
            ep_passes = cursor.fetchone()["ep_passes"] or 1

        score = lobby_model.predict(
            org["lobbying_cost"] or 1,
            ep_passes,
            org["members_fte"] or 1,
            org["country_code"],
            org["interest_represented"] or "",
        )
        score = round(score, 2)

        if score < 5:
            influence_class = "Low"
        elif score < 20:
            influence_class = "Medium"
        else:
            influence_class = "High"

        return jsonify({"influence_score": score, "influence_class": influence_class}), 200
    except ValueError as e:
        current_app.logger.warning(f"influence-prediction input error for org {org_id}: {e}")
        return error_response(str(e), 422)
    except Error as e:
        current_app.logger.error(f"Database error in get_org_influence_prediction: {e}")
        return error_response(str(e))


# Route 6 — GET /organizations/<org_id>/meetings
@organizations_bp.route("/organizations/<int:org_id>/meetings", methods=["GET"])
def get_org_meetings(org_id):
    current_app.logger.info(f"GET /organizations/{org_id}/meetings")
    try:
        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute("SELECT org_id FROM organization WHERE org_id = %s", (org_id,))
            if not cursor.fetchone():
                return error_response("Organization not found", 404)

            cursor.execute("""
                SELECT meeting_id, eu_body, meeting_date, subject, attendees_count, source
                FROM meeting
                WHERE org_id = %s
                ORDER BY meeting_date DESC
            """, (org_id,))
            meetings = cursor.fetchall()
        return jsonify(meetings), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_org_meetings: {e}")
        return error_response(str(e))


# Route 7 — POST /meetings
@organizations_bp.route("/meetings", methods=["POST"])
def create_meeting():
    current_app.logger.info("POST /meetings")
    try:
        data = request.get_json()
        if "org_id" not in data:
            return error_response("Missing required field: org_id", 400)

        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute("SELECT org_id FROM organization WHERE org_id = %s", (data["org_id"],))
            if not cursor.fetchone():
                return error_response("Organization not found", 404)

            cursor.execute("""
                INSERT INTO meeting (org_id, eu_body, meeting_date, subject, attendees_count, source)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                data["org_id"],
                data.get("eu_body"),
                data.get("meeting_date"),
                data.get("subject"),
                data.get("attendees_count"),
                data.get("source"),
            ))
            new_id = cursor.lastrowid

        get_db().commit()
        return jsonify({"message": "Meeting created successfully", "meeting_id": new_id}), 201
    except Error as e:
        current_app.logger.error(f"Database error in create_meeting: {e}")
        return error_response(str(e))


# Route 8 — GET /organizations/<org_id>/access-passes
@organizations_bp.route("/organizations/<int:org_id>/access-passes", methods=["GET"])
def get_org_access_passes(org_id):
    current_app.logger.info(f"GET /organizations/{org_id}/access-passes")
    try:
        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute("SELECT org_id FROM organization WHERE org_id = %s", (org_id,))
            if not cursor.fetchone():
                return error_response("Organization not found", 404)

            cursor.execute("""
                SELECT pass_id, person_name, role_title, eu_body, issue_date, expiry_date, source
                FROM access_pass
                WHERE org_id = %s
                ORDER BY issue_date DESC
            """, (org_id,))
            passes = cursor.fetchall()
            total = len(passes)

        return jsonify({"total": total, "passes": passes}), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_org_access_passes: {e}")
        return error_response(str(e))


# Route 9 — GET /organizations/<org_id>/expenditures
@organizations_bp.route("/organizations/<int:org_id>/expenditures", methods=["GET"])
def get_org_expenditures(org_id):
    current_app.logger.info(f"GET /organizations/{org_id}/expenditures")
    try:
        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute("SELECT org_id FROM organization WHERE org_id = %s", (org_id,))
            if not cursor.fetchone():
                return error_response("Organization not found", 404)

            cursor.execute("""
                SELECT expenditure_id, year, amount_eur, amount_range_min_eur,
                       amount_range_max_eur, currency, source
                FROM expenditure_record
                WHERE org_id = %s
                ORDER BY year DESC
            """, (org_id,))
            expenditures = cursor.fetchall()

        return jsonify(expenditures), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_org_expenditures: {e}")
        return error_response(str(e))


# Route 10 — POST /organizations/<org_id>/expenditures
@organizations_bp.route("/organizations/<int:org_id>/expenditures", methods=["POST"])
def create_expenditure(org_id):
    current_app.logger.info(f"POST /organizations/{org_id}/expenditures")
    try:
        data = request.get_json()
        if "year" not in data or "amount_eur" not in data:
            return error_response("Missing required fields: year, amount_eur", 400)

        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute("SELECT org_id FROM organization WHERE org_id = %s", (org_id,))
            if not cursor.fetchone():
                return error_response("Organization not found", 404)

            cursor.execute("""
                INSERT INTO expenditure_record
                    (org_id, year, amount_eur, amount_range_min_eur, amount_range_max_eur, currency, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                org_id,
                data["year"],
                data["amount_eur"],
                data.get("amount_range_min_eur"),
                data.get("amount_range_max_eur"),
                data.get("currency", "EUR"),
                data.get("source"),
            ))
            new_id = cursor.lastrowid

        get_db().commit()
        return jsonify({"message": "Expenditure record created", "expenditure_id": new_id}), 201
    except Error as e:
        current_app.logger.error(f"Database error in create_expenditure: {e}")
        return error_response(str(e))


# Route 11 — DELETE /expenditures/<expenditure_id>
@organizations_bp.route("/expenditures/<int:expenditure_id>", methods=["DELETE"])
def delete_expenditure(expenditure_id):
    current_app.logger.info(f"DELETE /expenditures/{expenditure_id}")
    try:
        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT expenditure_id FROM expenditure_record WHERE expenditure_id = %s",
                (expenditure_id,)
            )
            if not cursor.fetchone():
                return error_response("Expenditure record not found", 404)
            cursor.execute(
                "DELETE FROM expenditure_record WHERE expenditure_id = %s", (expenditure_id,)
            )
        get_db().commit()
        return jsonify({"message": "Expenditure record deleted"}), 200
    except Error as e:
        current_app.logger.error(f"Database error in delete_expenditure: {e}")
        return error_response(str(e))


# Route 12 — GET /lobbying-activities
@organizations_bp.route("/lobbying-activities", methods=["GET"])
def get_lobbying_activities():
    current_app.logger.info("GET /lobbying-activities")
    try:
        org_id      = request.args.get("org_id")
        policy_area = request.args.get("policy_area")
        limit       = min(int(request.args.get("limit", 100)), 500)

        query = """
            SELECT la.activity_id, la.org_id, o.name AS org_name,
                   la.activity_type, la.eu_institution, la.start_date,
                   pa.name AS policy_area
            FROM lobbying_activity la
            JOIN organization o ON la.org_id = o.org_id
            LEFT JOIN policy_area pa ON la.policy_area_id = pa.policy_area_id
            WHERE 1=1
        """
        params = []

        if org_id:
            query += " AND la.org_id = %s"
            params.append(int(org_id))
        if policy_area:
            query += " AND pa.name = %s"
            params.append(policy_area)

        query += " ORDER BY la.start_date DESC LIMIT %s"
        params.append(limit)

        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute(query, params)
            activities = cursor.fetchall()

        return jsonify(activities), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_lobbying_activities: {e}")
        return error_response(str(e))


# Route 13 — POST /organizations
@organizations_bp.route("/organizations", methods=["POST"])
def create_organization():
    current_app.logger.info("POST /organizations")
    try:
        data = request.get_json()

        required_fields = ["name", "country_code", "lobbying_cost"]
        for field in required_fields:
            if field not in data:
                return error_response(f"Missing required field: {field}", 400)

        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute("""
                INSERT INTO organization
                    (name, members_eu, members_fte, lobbying_cost,
                     interest_represented, country_code, industry_id, lobbyfacts_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data["name"],
                data.get("members_eu"),
                data.get("members_fte"),
                data["lobbying_cost"],
                data.get("interest_represented"),
                data["country_code"],
                data.get("industry_id"),
                data.get("lobbyfacts_url"),
            ))
            new_id = cursor.lastrowid

        get_db().commit()
        current_app.logger.info(f"Created organization id={new_id}")
        return jsonify({"message": "Organization created successfully", "org_id": new_id}), 201
    except Error as e:
        current_app.logger.error(f"Database error in create_organization: {e}")
        return error_response(str(e))


# Route 14 — PUT /organizations/<org_id>
@organizations_bp.route("/organizations/<int:org_id>", methods=["PUT"])
def update_organization(org_id):
    current_app.logger.info(f"PUT /organizations/{org_id}")
    try:
        data = request.get_json()

        allowed_fields = [
            "name", "members_eu", "members_fte", "lobbying_cost",
            "interest_represented", "country_code", "industry_id", "lobbyfacts_url"
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


# Route 15 — DELETE /organizations/<org_id>
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


# Route 16 — GET /policy-areas
@organizations_bp.route("/policy-areas", methods=["GET"])
def get_policy_areas():
    current_app.logger.info("GET /policy-areas")
    try:
        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT policy_area_id, name, description FROM policy_area ORDER BY name"
            )
            areas = cursor.fetchall()
        return jsonify(areas), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_policy_areas: {e}")
        return error_response(str(e))


# Route 17 — GET /analytics/policy-area-stats
@organizations_bp.route("/analytics/policy-area-stats", methods=["GET"])
def get_policy_area_stats():
    current_app.logger.info("GET /analytics/policy-area-stats")
    try:
        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT pa.name AS policy_area,
                       COUNT(DISTINCT la.org_id)   AS org_count,
                       COUNT(la.activity_id)        AS activity_count,
                       COALESCE(AVG(o.lobbying_cost), 0) AS avg_lobbying_cost
                FROM policy_area pa
                LEFT JOIN lobbying_activity la ON pa.policy_area_id = la.policy_area_id
                LEFT JOIN organization o       ON la.org_id = o.org_id
                GROUP BY pa.policy_area_id, pa.name
                ORDER BY org_count DESC
            """)
            stats = cursor.fetchall()
        return jsonify(stats), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_policy_area_stats: {e}")
        return error_response(str(e))


# Route 18 — GET /analytics/country-stats
@organizations_bp.route("/analytics/country-stats", methods=["GET"])
def get_country_stats():
    current_app.logger.info("GET /analytics/country-stats")
    try:
        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT
                    o.country_code,
                    COUNT(*)                          AS org_count,
                    COALESCE(SUM(o.lobbying_cost), 0) AS total_spend,
                    COALESCE(AVG(o.lobbying_cost), 0) AS avg_spend,
                    COALESCE(MAX(o.lobbying_cost), 0) AS max_spend
                FROM organization o
                WHERE o.country_code IS NOT NULL
                GROUP BY o.country_code
                ORDER BY total_spend DESC
            """)
            stats = cursor.fetchall()
        return jsonify(stats), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_country_stats: {e}")
        return error_response(str(e))
