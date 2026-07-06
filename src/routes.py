from typing import Any, cast

from flask import Blueprint, jsonify, request

from src.database import db
from src.decorators import login_required
from src.models import Movie, User

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/favorites", methods=["POST"])
@login_required
def add_favorite() -> Any:
	"""
	Endpoint to add a movie to the authenticated user's favorites.
	Strictly validates incoming JSON payloads.
	"""
	data = request.get_json()
	
	# Defensive Guard Clause: Ensure payload exists and contains required fields
	if not data or "imdb_id" not in data or "title" not in data:
		return jsonify({"error": "Invalid data"}), 400
	
	current_user = cast(User, getattr(request, "user"))
	
	new_movie = Movie(
			imdb_id=data["imdb_id"],
			title=data["title"],
			user_id=current_user.id
	)
	
	try:
		db.session.add(new_movie)
		db.session.commit()
	except Exception as e:
		db.session.rollback()
		# Fallback error handling (should ideally be caught by @route_error_handler)
		return jsonify({"error": "Database transaction failed"}), 500
	
	return jsonify({"id": new_movie.id}), 201
