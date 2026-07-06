from flask import Blueprint, jsonify, request, session
from sqlalchemy import select

from src.database import db
from src.models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
	data = request.get_json()
	if not data or "username" not in data or "password" not in data:
		return jsonify({"error": "Missing data"}), 400
	
	stmt = select(User).where(User.username == data["username"])
	if db.session.execute(stmt).scalar_one_or_none():
		return jsonify({"error": "User exists"}), 409
	
	new_user = User(username=data["username"])
	new_user.password = data["password"]
	db.session.add(new_user)
	db.session.commit()
	return jsonify({"message": "User created"}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
	data = request.get_json()
	if not data or "username" not in data or "password" not in data:
		return jsonify({"error": "Missing credentials"}), 400
	
	stmt = select(User).where(User.username == data["username"])
	user = db.session.execute(stmt).scalar_one_or_none()
	
	if user and user.check_password(data["password"]):
		session["user_id"] = str(user.id)
		return jsonify({"message": "Logged in"}), 200
	
	return jsonify({"error": "Invalid credentials"}), 401
