import logging
logger = logging.getLogger(__name__)

from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from backend.utils import error_response
from mysql.connector import Error

users_bp = Blueprint("users", __name__)


# Route 8 — GET /preferences
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