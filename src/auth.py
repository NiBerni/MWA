from typing import Any, cast

from flask import Blueprint, jsonify, request, session
from sqlalchemy import select

from src.database import db
from src.decorators import login_required
from src.models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["POST"])
def register() -> Any:
	"""Register a new user with their custom OMDb API key."""
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
	"""Authenticates the user and initiates a session."""
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
	"""Updates the authenticated user's password and/or OMDb API Key."""
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
	Deletes the authenticated user.
	Leverages the ORM db.session.delete() to trigger SQLAlchemy cascades,
	ensuring all related favorite movies are also securely wiped.
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
	"""Securely terminates the user session."""
	session.clear()
	return jsonify({"message": "Logged out successfully"}), 200
