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
	Renders the Start Page.
	If the user is already authenticated via our custom session flow,
	redirect them to their favorites.
	"""
	# Defensive Check: If 'user_id' is in the session, they are logged in.
	if "user_id" in session:
		return redirect(url_for("views.favorites"))
	
	return render_template("index.html")


@views_bp.route("/register")
def register() -> Any:
	"""
	Renders the Registration Page.
	Defensively redirects authenticated users to the dashboard.
	"""
	if "user_id" in session:
		return redirect(url_for("views.favorites"))
	
	return render_template("register.html")


@views_bp.route("/favorites")
@login_required
def favorites() -> Any:
	"""
	Renders the user's favorite movies.
	If the user has no favorites, redirects them to the Add Movie page.
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
	Renders the Add Movie search interface.
	"""
	return render_template("add_movie.html")


@views_bp.route("/profile")
@login_required
def profile() -> Any:
	"""
	Renders the User Profile management page.
	"""
	return render_template("profile.html")
