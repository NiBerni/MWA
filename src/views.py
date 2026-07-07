from typing import Any

from flask import Blueprint, redirect, render_template, request, session, url_for
from sqlalchemy import select

from src.database import db
from src.decorators import login_required
from src.models import Movie

views_bp = Blueprint("views", __name__)


@views_bp.route("/")
def index() -> Any:
	"""
	Redirect to the user's favorite page if they are logged in.

	:return: A redirect response to the favorite page or a rendered index template.
	:rtype: Any
	"""
	# Defensive Check: If 'user_id' is in the session, they are logged in.
	if "user_id" in session:
		return redirect(url_for("views.favorites"))
	
	return render_template("index.html")


@views_bp.route("/register")
def register() -> Any:
	"""Execute the registration page.

	This view handles rendering of the registration form and redirects logged-in users to their favorites page.
	:return: A rendered HTML template if not logged in, or a redirect response if logged in.
	:rtype: Any
	"""
	if "user_id" in session:
		return redirect(url_for("views.favorites"))
	
	return render_template("register.html")


@views_bp.route("/favorites")
@login_required
def favorites() -> Any:
	"""
	Display the list of favorite movies for the current user.

	This view function retrieves the list of movies that have been marked as favorites by the currently logged-in user. If the user is not authenticated, the function redirects to the main index page. If no favorite movies are found, it redirects to a page where users can add movies.

	:return: A rendered HTML template displaying the list of favorite movies or redirects.
	:rtype: Any
	"""
	active_user = getattr(request, "user", None)
	
	if not active_user:
		return redirect(url_for("views.index"))
	
	stmt = select(Movie).where(Movie.user_id == active_user.id)
	user_movies = db.session.execute(stmt).scalars().all()
	
	if not user_movies:
		return redirect(url_for("views.add_movie"))
	
	return render_template("favorites.html", movies=user_movies)


@views_bp.route("/add-movie")
@login_required
def add_movie() -> Any:
	"""

	Render the "add_movie" template for adding a new movie.

	:return: HTML template for adding a new movie

	"""
	return render_template("add_movie.html")


@views_bp.route("/profile")
@login_required
def profile() -> Any:
	"""
	Render the user's profile page.

	:return: The rendered HTML template for the user's profile.
	:rtype: Any
	"""
	return render_template("profile.html")
