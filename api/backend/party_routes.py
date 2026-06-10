import logging
logger = logging.getLogger(__name__)

from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from backend.utils import error_response
from mysql.connector import Error

parties_bp = Blueprint("parties", __name__)


# Route 1 — GET /parties
@parties_bp.route("/parties", methods=["GET"])
def get_all_parties():
    current_app.logger.info("GET /parties")
    try:
        country     = request.args.get("country")
        ep_party    = request.args.get("ep_party")
        limit       = int(request.args.get("limit", 50))

        query = """
            SELECT party_id, party_name_english, country_name, populist,
                   farright, farleft, eurosceptic, in_parliament, family_name,
                   left_right, state_market, liberty_authority, eu_anti_pro,
                   ep_party
            FROM party_info
            WHERE 1=1
        """
        params = []

        if country:
            query += " AND country_name = %s"
            params.append(country)
        if ep_party:
            query += " AND ep_party = %s"
            params.append(ep_party)

        query += " ORDER BY left_right DESC LIMIT %s"
        params.append(limit)

        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute(query, params)
            parties = cursor.fetchall()

        current_app.logger.info(f"Retrieved {len(parties)} parties")
        return jsonify(parties), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_all_parties: {e}")
        return error_response(str(e))


# Route 2 — GET /parties/lobby-info
@parties_bp.route("/parties/lobby-info", methods=["GET"])
def get_party_lobby_info():
    current_app.logger.info("GET /parties/lobby-info")
    try:
        ep_party = request.args.get("ep_party")

        query = """
            SELECT ep_party, lobbyists, meetings_per_lobbyist, total_meetings
            FROM party_to_lobby_info
            WHERE 1=1
        """
        params = []

        if ep_party:
            query += " AND ep_party = %s"
            params.append(ep_party)

        query += " ORDER BY total_meetings DESC"

        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute(query, params)
            lobby_info = cursor.fetchall()

        current_app.logger.info(f"Retrieved {len(lobby_info)} lobby info records")
        return jsonify(lobby_info), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_party_lobby_info: {e}")
        return error_response(str(e))
    
    