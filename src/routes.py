from typing import Any, cast

from flask import Blueprint, jsonify, request
from sqlalchemy import select, tstring

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


@api_bp.route("/favorites", methods=["GET"])
@login_required
def get_favorites() -> Any:
	"""
	Retrieve all favorite movies for the currently authenticated user.
	"""
	current_user = cast(User, getattr(request, "user"))
	
	# SQLAlchemy 2.0 execute style
	stmt = select(Movie).where(Movie.user_id == current_user.id)
	movies = db.session.execute(stmt).scalars().all()
	
	movie_list = [
			{
					"id":      m.id,
					"imdb_id": m.imdb_id,
					"title":   m.title,
					"year":    m.year,
					"rating":  m.rating,
					"genre":   m.genre
			}
			for m in movies
	]
	
	return jsonify(movie_list), 200


@api_bp.route("/favorites/<int:movie_id>", methods=["PATCH"])
@login_required
def update_favorite(movie_id: int) -> Any:
	"""
	Update details (e.g., rating, genre) of a specific favorite movie.
	Strictly verifies ownership to prevent IDOR attacks.
	"""
	current_user = cast(User, getattr(request, "user"))
	data = request.get_json()
	
	if not data:
		return jsonify({"error": "Invalid data payload"}), 400
	
	# Find the movie AND ensure it belongs to the current user
	stmt = select(Movie).where(
			Movie.id == movie_id,
			Movie.user_id == current_user.id
	)
	movie = db.session.execute(stmt).scalar_one_or_none()
	
	if not movie:
		# Returning 404 instead of 403 prevents attackers from scanning valid movie IDs
		return jsonify({"error": "Movie not found"}), 404
	
	# Update allowed fields
	if "rating" in data:
		movie.rating = str(data["rating"])
	if "genre" in data:
		movie.genre = str(data["genre"])
	
	try:
		db.session.commit()
	except Exception as e:
		db.session.rollback()
		return jsonify({"error": "Database update failed"}), 500
	
	return jsonify({
			"message": "Movie updated successfully",
			"movie":   {
					"id":     movie.id,
					"rating": movie.rating,
					"genre":  movie.genre
			}
	}), 200


@api_bp.route("/favorites/<int:movie_id>", methods=["DELETE"])
@login_required
def delete_favorite(movie_id: int) -> Any:
	"""
	Remove a movie from the user's favorites.
	Utilizes SQLAlchemy's modern PEP 750 t-string processor for secure raw SQL execution.
	"""
	current_user = cast(User, getattr(request, "user"))
	
	try:
		delete_query = tstring(t"DELETE FROM movies WHERE id = {movie_id} AND user_id = {current_user.id}")
		
		result = db.session.execute(delete_query)
		db.session.commit()
		
		if result.rowcount == 0:
			return jsonify({"error": "Movie not found or unauthorized"}), 404
	
	except Exception as e:
		db.session.rollback()
		return jsonify({"error": "Failed to delete movie"}), 500
	
	return "", 204  # 204 No Content is standard for successful deletions
