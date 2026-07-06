from flask import Blueprint, jsonify, request

from src.database import db
from src.models import User

auth_bp = Blueprint("/auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
	data = request.get_json()
	if not data or "username" not in data or "password" not in data:
		return jsonify({"error": "Missing data"}), 400
	if User.query.filter_by(username=data["username"]).first():
		return jsonify({"error": "User exists"}), 409
	
	new_user = User(username=data["username"])
	new_user.password = data["password"]
	db.session.add(new_user)
	db.session.commit()
	return jsonify({"message": "User created"})
