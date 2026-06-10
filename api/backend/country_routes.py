import logging
logger = logging.getLogger(__name__)

from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from backend.utils import error_response
from mysql.connector import Error

countries_bp = Blueprint("countries", __name__)


# Route 19 — GET /country-indicators
@countries_bp.route("/country-indicators", methods=["GET"])
def get_all_country_indicators():
    current_app.logger.info("GET /country-indicators")
    try:
        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT ci.country, ci.country_code, ci.gdp_usd, ci.population,
                       ci.inflation, ci.gdp_per_capita,
                       COUNT(o.org_id)                   AS org_count,
                       COALESCE(SUM(o.lobbying_cost), 0) AS total_lobbying_spend
                FROM country_indicator ci
                LEFT JOIN organization o ON o.country_code = ci.country
                GROUP BY ci.country, ci.country_code, ci.gdp_usd,
                         ci.population, ci.inflation, ci.gdp_per_capita
                ORDER BY total_lobbying_spend DESC
            """)
            countries = cursor.fetchall()
        return jsonify(countries), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_all_country_indicators: {e}")
        return error_response(str(e))


# Route 20 — GET /country-indicators/<country_name>
@countries_bp.route("/country-indicators/<string:country_name>", methods=["GET"])
def get_country_indicators(country_name):
    current_app.logger.info(f"GET /country-indicators/{country_name}")
    try:
        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT country, country_code, gdp_usd, population, inflation, gdp_per_capita
                FROM country_indicator
                WHERE country = %s OR country_code = %s
            """, (country_name, country_name))
            country = cursor.fetchone()
            if not country:
                return error_response(f"Country '{country_name}' not found", 404)

            cursor.execute("""
                SELECT COUNT(*) AS org_count,
                       COALESCE(SUM(lobbying_cost), 0) AS total_lobbying_spend,
                       COALESCE(AVG(lobbying_cost), 0) AS avg_lobbying_spend
                FROM organization
                WHERE country_code = %s
            """, (country_name,))
            country["lobbying_summary"] = cursor.fetchone()

            cursor.execute("""
                SELECT org_id, name, lobbying_cost, interest_represented
                FROM organization
                WHERE country_code = %s
                ORDER BY lobbying_cost DESC
                LIMIT 10
            """, (country_name,))
            country["top_orgs"] = cursor.fetchall()

        return jsonify(country), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_country_indicators: {e}")
        return error_response(str(e))
