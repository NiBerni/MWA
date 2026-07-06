from typing import Any, cast

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import select, tstring

from src.database import db
from src.decorators import login_required, profile_query
from src.models import Movie, User
from src.omdb_client import OMDbAPIError, OMDbClient

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
	
	poster_url = data.get("poster_url")
	if poster_url == "N/A":
		poster_url = None
	
	new_movie = Movie(
			imdb_id=data["imdb_id"],
			title=data["title"],
			user_id=current_user.id,
			poster_url=poster_url
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
	stmt = select(Movie).where(
			Movie.id == movie_id,
			Movie.user_id == current_user.id
	)
	movie = db.session.execute(stmt).scalar_one_or_none()
	if not movie:
		# Returning 404 instead of 403 prevents attackers from scanning valid movie IDs
		return jsonify({"error": "Movie not found"}), 404
	
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


@api_bp.route("/favorites/search", methods=["GET"])
@login_required
@profile_query
def search_favorites() -> Any:
	"""
	Dynamic Search Endpoint.
	Filters by Genre, Director, and IMDb Rating boundaries.
	Features SQL-safe dynamic sorting via PEP 750 t-strings.
	"""
	current_user = cast(User, getattr(request, "user"))
	
	# Extract strings
	genre_filter = request.args.get("genre", default=None, type=str)
	author_filter = request.args.get("author", default=None, type=str)
	
	# Extract numerical boundaries
	min_rating = request.args.get("min_rating", default=None, type=float)
	max_rating = request.args.get("max_rating", default=None, type=float)
	
	# Extract sort preference (default to highest rated first)
	sort_by = request.args.get("sort", default="rating_desc", type=str)
	
	try:
		search_query = tstring(t"""
	            SELECT m.id, m.imdb_id, m.title, m.year, m.rating, m.genre, d.name AS director_name
	            FROM movies m
	            LEFT JOIN directors d ON m.director_id = d.id
	            WHERE m.user_id = {current_user.id}
	            AND ({genre_filter} IS NULL OR m.genre LIKE '%' || {genre_filter} || '%')
	            AND ({author_filter} IS NULL OR d.name LIKE '%' || {author_filter} || '%')
	            AND ({min_rating} IS NULL OR CAST(m.rating AS FLOAT) >= {min_rating})
	            AND ({max_rating} IS NULL OR CAST(m.rating AS FLOAT) <= {max_rating})
	            ORDER BY
	                CASE WHEN {sort_by} = 'rating_desc' THEN CAST(m.rating AS FLOAT) END DESC,
	                CASE WHEN {sort_by} = 'rating_asc' THEN CAST(m.rating AS FLOAT) END ASC,
	                CASE WHEN {sort_by} = 'title_asc' THEN m.title END ASC,
	                CAST(m.rating AS FLOAT) DESC -- Fallback default
	        """)
		
		# Execute the raw parameterized query
		result = db.session.execute(search_query).mappings().all()
		
		# Format the response
		movie_list = [
				{
						"id":       row["id"],
						"imdb_id":  row["imdb_id"],
						"title":    row["title"],
						"year":     row["year"],
						"rating":   row["rating"],
						"genre":    row["genre"],
						"director": row["director_name"]
				}
				for row in result
		]
		
		return jsonify(movie_list), 200
	
	except Exception as e:
		import logging
		logging.getLogger(__name__).error(f"Search query failed: {e}", exc_info=True)
		return jsonify({"error": "Failed to process search query"}), 500


@api_bp.route("/movies/search", methods=["GET"])
@login_required
@profile_query
def search_movie_tree() -> Any:
	"""
	Search Tree for new movies.
	1. Fetches from OMDb.
	2. Applies filters (Genre, Rating, Director) locally.
	3. Sorts based on user preference.
	"""
	# 1. Extract parameters
	title = request.args.get("title", "")
	genre_filter = request.args.get("genre")
	director_filter = request.args.get("director")
	min_rating = request.args.get("min_rating", type=float)
	max_rating = request.args.get("max_rating", type=float)
	sort_by = request.args.get("sort", default="rating_desc")
	
	if not title:
		return jsonify({"error": "Title is required"}), 400
	
	api_key = current_app.config.get("OMDB_API_KEY", "your_default_key")
	client = OMDbClient(api_key=api_key)
	
	try:
		movies = client.search_movies(title)
	except OMDbAPIError as e:
		return jsonify({"error": str(e)}), 400
	
	filtered_movies = []
	for movie in movies:
		try:
			detail = client.fetch_movie_by_id(movie["imdbID"])
		except OMDbAPIError:
			continue
		
		if genre_filter and genre_filter.lower() not in detail.get("Genre", "").lower():
			continue
		
		if director_filter and director_filter.lower() not in detail.get("Director", "").lower():
			continue
		
		try:
			rating = float(detail.get("imdbRating", 0))
		except ValueError:
			rating = 0.0
		
		if min_rating is not None and rating < min_rating:
			continue
		if max_rating is not None and rating > max_rating:
			continue
		
		filtered_movies.append(detail)
	
	if sort_by == "rating_desc":
		filtered_movies.sort(key=lambda x: float(x.get("imdbRating", 0)), reverse=True)
	elif sort_by == "rating_asc":
		filtered_movies.sort(key=lambda x: float(x.get("imdbRating", 0)))
	elif sort_by == "title_asc":
		filtered_movies.sort(key=lambda x: x.get("Title", "").lower())
	
	# 5. Return JSON response
	return jsonify(filtered_movies), 200
