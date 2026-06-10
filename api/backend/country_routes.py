import logging
logger = logging.getLogger(__name__)

from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from backend.utils import error_response
from mysql.connector import Error

countries_bp = Blueprint("countries", __name__)


# Route 7 — GET /country-indicators/<country_name>
@countries_bp.route("/country-indicators/<string:country_name>", methods=["GET"])
def get_country_indicators(country_name):
    current_app.logger.info(f"GET /country-indicators/{country_name}")
    try:
        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT * FROM country WHERE country_code = %s", (country_name,)
            )
            country = cursor.fetchone()
            if not country:
                return error_response(f"Country '{country_name}' not found", 404)

            cursor.execute(
                """SELECT year, gdp_usd, fossil_fuels, co2_emit, urban_pop
                   FROM country_indicator
                   WHERE country_code = %s
                   ORDER BY year DESC""",
                (country_name,)
            )
            country["indicators"] = cursor.fetchall()

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