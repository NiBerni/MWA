from typing import Any, cast

from flask import Blueprint, jsonify, request, session
from sqlalchemy import select

from src.database import db
from src.decorators import login_required
from src.models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["POST"])
def register() -> Any:
	"""Register a new user.

	Registers a new user with the provided username, password, and OMDB API key. The function performs several checks before creating a new user:

	1. Verifies that all required data fields (username, password, and OMDB API key) are present in the request JSON.
	2. Checks if the username already exists in the database to avoid duplicate entries.

	If any of these conditions are not met, an appropriate error message is returned with the corresponding HTTP status code. If the user creation is successful, a success message is returned with a 201 Created status code. In case of any exceptions during the registration process (e.g., database errors), the function logs the exception and returns a failure message with a 500 Internal Server Error status code.

	:param data: JSON data containing user information.
	:type data: dict
	:return: A JSON response indicating the result of the registration attempt.
	:rtype: Flask.Response
	"""
	data = request.get_json()
	
	# Defensive Guard Clause
	if not data or not all(k in data for k in ("username", "password", "omdb_api_key")):
		return jsonify({"error": "Missing required data fields"}), 400
	
	stmt = select(User).where(User.username == data["username"])
	if db.session.execute(stmt).scalar_one_or_none():
		return jsonify({"error": "Username already exists"}), 409
	
	try:
		new_user = User(username=data["username"])
		new_user.password = data["password"]
		new_user.omdb_api_key = data["omdb_api_key"]  # Triggers Fernet encryption
		
		db.session.add(new_user)
		db.session.commit()
		return jsonify({"message": "User created successfully"}), 201
	except Exception as e:
		db.session.rollback()
		# Standard f-string for logging
		import logging
		logging.getLogger(__name__).error(f"Registration failed: {e}", exc_info=True)
		return jsonify({"error": "Failed to register user"}), 500


@auth_bp.route("/login", methods=["POST"])
def login() -> Any:
	"""
	Execute the login process for a user.

	This function handles the POST request to the "/login" endpoint, which is responsible for authenticating a user based on provided username and password. If the credentials are valid, it sets the user ID in the session and returns a success message. Otherwise, it returns an error message indicating invalid credentials.

	:param data: JSON data containing username and password
	:type data: dict
	:return: A tuple containing the response JSON and HTTP status code
	:rtype: Tuple[dict, int]
	"""
	data = request.get_json()
	if not data or "username" not in data or "password" not in data:
		return jsonify({"error": "Missing credentials"}), 400
	
	stmt = select(User).where(User.username == data["username"])
	user = db.session.execute(stmt).scalar_one_or_none()
	
	if user and user.check_password(data["password"]):
		session["user_id"] = str(user.id)
		return jsonify({"message": "Logged in successfully"}), 200
	
	return jsonify({"error": "Invalid credentials"}), 401


@auth_bp.route("/profile", methods=["PATCH"])
@login_required
def update_profile() -> Any:
	"""
	Update the authenticated user's profile.

	This view function handles PATCH requests at '/profile' endpoint and allows updating of the current user's password or OMDB API key. It ensures that only valid JSON payloads are processed and updates the specified fields in the database atomically.

	:param data: A dictionary containing the request body with possible keys 'password' and 'omdb_api_key'.
	:type data: dict

	:return: A JSON response indicating success or failure of the profile update.
	:rtype: Flask.Response
	"""
	current_user = cast(User, getattr(request, "user"))
	data = request.get_json()
	
	if not data:
		return jsonify({"error": "Invalid JSON payload"}), 400
	
	# Dynamically update provided fields
	if "password" in data and data["password"].strip():
		current_user.password = data["password"]
	
	if "omdb_api_key" in data and data["omdb_api_key"].strip():
		current_user.omdb_api_key = data["omdb_api_key"]
	
	try:
		db.session.commit()
		return jsonify({"message": "Profile updated successfully"}), 200
	except Exception as e:
		db.session.rollback()
		import logging
		logging.getLogger(__name__).error(f"Failed to update profile for {current_user.id}: {e}")
		return jsonify({"error": "Database update failed"}), 500


@auth_bp.route("/profile", methods=["DELETE"])
@login_required
def delete_profile() -> Any:
	"""
	Delete the current user's profile.

	:return: An empty response with status code 204 if the deletion is successful.
	:rtype: Tuple[None, int]

	:raises Exception: If an error occurs during the deletion process.
	"""
	current_user = cast(User, getattr(request, "user"))
	
	try:
		db.session.delete(current_user)
		db.session.commit()
		
		# Invalidate the session securely
		session.clear()
		
		return "", 204  # 204 No Content
	except Exception as e:
		db.session.rollback()
		import logging
		logging.getLogger(__name__).error(f"Failed to delete profile for {current_user.id}: {e}")
		return jsonify({"error": "Failed to delete account"}), 500


@auth_bp.route("/logout", methods=["POST"])
def logout() -> Any:
	"""
	Logout the user.
	
	Clears the session and returns a JSON response indicating successful logout.
	"""
	session.clear()
	return jsonify({"message": "Logged out successfully"}), 200
