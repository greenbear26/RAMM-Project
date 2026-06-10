import logging
logger = logging.getLogger(__name__)
 
from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from backend.utils import error_response
from mysql.connector import Error
 
organizations_bp = Blueprint("organizations", __name__)
 
 
# test route
@organizations_bp.route("/test", methods=["GET"])
def test_route():
    current_app.logger.info("GET /test")
    query = "select country from country_indicator;"
    with get_db().cursor(dictionary=True) as cursor:
        cursor.execute(query)
        countries = cursor.fetchall()
    return jsonify(countries), 200
 
 
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
 
        query  = """
            SELECT DISTINCT org_id, name, members_fte,
                   lobbying_cost, interest_represented, country_name,
                   all_ep_passes, ep_meetings, policy_areas
            FROM lobbying_organization
            WHERE 1=1
        """
        params = []
 
        if country:
            query += " AND country_name = %s"
            params.append(country)
        if policy_area:
            query += " AND policy_areas LIKE %s"
            params.append(f"%{policy_area}%")
        if interest:
            query += " AND interest_represented LIKE %s"
            params.append(f"%{interest}%")
        if min_cost:
            query += " AND lobbying_cost >= %s"
            params.append(float(min_cost))
        if max_cost:
            query += " AND lobbying_cost <= %s"
            params.append(float(max_cost))
        if name:
            query += " AND name LIKE %s"
            params.append(f"%{name}%")
 
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
 
 
# Route 2 — GET /organizations/<org_id>
@organizations_bp.route("/organizations/<int:org_id>", methods=["GET"])
def get_organization(org_id):
    current_app.logger.info(f"GET /organizations/{org_id}")
    try:
        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute(
                """SELECT org_id, name, members_fte,
                   lobbying_cost, interest_represented, country_name,
                   all_ep_passes, ep_meetings, policy_areas
                   FROM lobbying_organization WHERE org_id = %s""",
                (org_id,)
            )
            org = cursor.fetchone()
            if not org:
                return error_response("Organization not found", 404)
 
            cursor.execute(
                "SELECT year, amount_eur FROM expenditure_record WHERE org_id = %s ORDER BY year DESC",
                (org_id,)
            )
            org["expenditures"] = cursor.fetchall()
 
            cursor.execute(
                """SELECT la.activity_type, la.eu_institution, la.start_date,
                          pa.name AS policy_area
                   FROM lobbying_activity la
                   LEFT JOIN policy_area pa ON la.policy_area_id = pa.policy_area_id
                   WHERE la.org_id = %s""",
                (org_id,)
            )
            org["lobbying_activities"] = cursor.fetchall()
 
            cursor.execute(
                "SELECT COUNT(*) AS meeting_count FROM meeting WHERE org_id = %s",
                (org_id,)
            )
            org["meetings"] = cursor.fetchone()["meeting_count"]
 
        return jsonify(org), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_organization: {e}")
        return error_response(str(e))
 
 
# Route 3 — POST /organizations
@organizations_bp.route("/organizations", methods=["POST"])
def create_organization():
    current_app.logger.info("POST /organizations")
    try:
        data = request.get_json()
 
        required_fields = ["name", "country_name", "lobbying_cost"]
        for field in required_fields:
            if field not in data:
                return error_response(f"Missing required field: {field}", 400)
 
        query = """
            INSERT INTO lobbying_organization
                (name, all_ep_passes, members_fte, lobbying_cost,
                 interest_represented, country_name, ep_meetings, policy_areas)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute(query, (
                data["name"],
                data.get("all_ep_passes"),
                data.get("members_fte"),
                data["lobbying_cost"],
                data.get("interest_represented"),
                data["country_name"],
                data.get("ep_meetings"),
                data.get("policy_areas"),
            ))
            new_id = cursor.lastrowid
 
        get_db().commit()
        current_app.logger.info(f"Created organization id={new_id}")
        return jsonify({"message": "Organization created successfully", "org_id": new_id}), 201
    except Error as e:
        current_app.logger.error(f"Database error in create_organization: {e}")
        return error_response(str(e))
 
 
# Route 4 — PUT /organizations/<org_id>
@organizations_bp.route("/organizations/<int:org_id>", methods=["PUT"])
def update_organization(org_id):
    current_app.logger.info(f"PUT /organizations/{org_id}")
    try:
        data = request.get_json()
 
        allowed_fields = [
            "name", "all_ep_passes", "members_fte", "lobbying_cost",
            "interest_represented", "country_name", "ep_meetings", "policy_areas"
        ]
        update_fields = [f"{f} = %s" for f in allowed_fields if f in data]
        params        = [data[f] for f in allowed_fields if f in data]
 
        if not update_fields:
            return error_response("No valid fields to update", 400)
 
        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute("SELECT org_id FROM lobbying_organization WHERE org_id = %s", (org_id,))
            if not cursor.fetchone():
                return error_response("Organization not found", 404)
 
            params.append(org_id)
            cursor.execute(
                f"UPDATE lobbying_organization SET {', '.join(update_fields)} WHERE org_id = %s",
                params
            )
 
        get_db().commit()
        return jsonify({"message": "Organization updated successfully"}), 200
    except Error as e:
        current_app.logger.error(f"Database error in update_organization: {e}")
        return error_response(str(e))
 
 
# Route 5 — DELETE /organizations/<org_id>
@organizations_bp.route("/organizations/<int:org_id>", methods=["DELETE"])
def delete_organization(org_id):
    current_app.logger.info(f"DELETE /organizations/{org_id}")
    try:
        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute("SELECT org_id FROM lobbying_organization WHERE org_id = %s", (org_id,))
            if not cursor.fetchone():
                return error_response("Organization not found", 404)
            cursor.execute("DELETE FROM lobbying_organization WHERE org_id = %s", (org_id,))
 
        get_db().commit()
        current_app.logger.info(f"Deleted organization id={org_id}")
        return jsonify({"message": "Organization deleted successfully"}), 200
    except Error as e:
        current_app.logger.error(f"Database error in delete_organization: {e}")
        return error_response(str(e))
 
 
# Route 6 — GET /policy-areas
@organizations_bp.route("/policy-areas", methods=["GET"])
def get_policy_areas():
    current_app.logger.info("GET /policy-areas")
    try:
        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT policy_areas FROM lobbying_organization"
            )
            areas = cursor.fetchall()
        return jsonify(areas), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_policy_areas: {e}")
        return error_response(str(e))