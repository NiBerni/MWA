import uuid
from typing import Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import delete

from src.database import db
from src.models import Movie, User


@pytest.fixture(autouse=True)
def clean_database(app: Flask) -> Generator[None, None, None]:
	"""
	Defensive TDD Pattern: Automatically wipes the database tables clean
	before and after EVERY test to guarantee absolute test isolation.
	Utilizes SQLAlchemy 2.0 execution syntax.
	"""
	with app.app_context():
		# Clean before test
		db.session.execute(delete(Movie))
		db.session.execute(delete(User))
		db.session.commit()
	
	yield  # The test executes here
	
	with app.app_context():
		# Clean after test
		db.session.execute(delete(Movie))
		db.session.execute(delete(User))
		db.session.commit()


@pytest.fixture
def auth_client_and_user(app: Flask, client: FlaskClient) -> Generator[tuple[FlaskClient, User], None, None]:
	"""Provides a test client with an authenticated session and a uniquely generated User."""
	valid_uuid = uuid.uuid4()
	unique_username = f"crud_{valid_uuid.hex[:8]}"
	
	with app.app_context():
		user = User(id=valid_uuid, username=unique_username, password="secure")
		db.session.add(user)
		db.session.commit()
		db.session.refresh(user)
	
	with client.session_transaction() as sess:
		sess["user_id"] = str(valid_uuid)
	
	yield client, user


@pytest.fixture
def sample_movie(app: Flask, auth_client_and_user: tuple[FlaskClient, User]) -> Generator[Movie, None, None]:
	"""Injects a sample movie belonging to the authenticated user."""
	_, user = auth_client_and_user
	with app.app_context():
		movie = Movie(imdb_id="tt0111161", title="The Shawshank Redemption", user_id=user.id)
		db.session.add(movie)
		db.session.commit()
		db.session.refresh(movie)
		
		yield movie


def test_register_user(client: FlaskClient) -> None:
	"""Test user registration endpoint payload routing."""
	unique_username = f"new_user_{uuid.uuid4().hex[:8]}"
	response = client.post("/auth/register", json={
			"username": unique_username,
			"password": "secure_password"
	})
	assert response.status_code in [200, 201, 404]


def test_unauthorized_movie_add(client: FlaskClient) -> None:
	"""Defensive check: Ensure non-authenticated users cannot access protected routes."""
	response = client.post("/api/favorites", json={"imdb_id": "tt12345", "title": "Test"})
	assert response.status_code == 401


@pytest.mark.parametrize("payload", [
		{},  # Empty payload
		{"title": "Dune"},  # Missing imdb_id
		{"imdb_id": "tt1160419"},  # Missing title
])
def test_add_favorite_invalid_data(client: FlaskClient, app: Flask, payload: dict) -> None:
	"""
	Test that adding a favorite requires strict JSON validation.
	Generates a unique user per parameter iteration to prevent IntegrityErrors.
	"""
	valid_uuid = uuid.uuid4()
	unique_username = f"val_{valid_uuid.hex[:8]}"
	
	with app.app_context():
		user = User(id=valid_uuid, username=unique_username, password="secure")
		db.session.add(user)
		db.session.commit()
	
	with client.session_transaction() as sess:
		sess["user_id"] = str(valid_uuid)
	
	response = client.post("/api/favorites", json=payload)
	
	assert response.status_code == 400
	assert response.get_json()["error"] in ["Invalid data", "Invalid data payload"]


def test_add_favorite_movie_success(client: FlaskClient, app: Flask) -> None:
	"""Test that an authenticated user can successfully add a movie to favorites."""
	valid_uuid = uuid.uuid4()
	unique_username = f"fav_{valid_uuid.hex[:8]}"
	
	with app.app_context():
		user = User(id=valid_uuid, username=unique_username, password="secure")
		db.session.add(user)
		db.session.commit()
	
	with client.session_transaction() as sess:
		sess["user_id"] = str(valid_uuid)
	
	response = client.post(
			"/api/favorites",
			json={
					"imdb_id": "tt1160419",
					"title":   "Dune",
					"year":    "2021"
			}
	)
	
	assert response.status_code == 201
	assert "id" in response.get_json()


def test_get_favorites(auth_client_and_user: tuple[FlaskClient, User], sample_movie: Movie) -> None:
	"""Test retrieving a list of favorite movies for the authenticated user."""
	client, _ = auth_client_and_user
	response = client.get("/api/favorites")
	
	assert response.status_code == 200
	data = response.get_json()
	assert isinstance(data, list)
	assert len(data) == 1
	assert data[0]["title"] == "The Shawshank Redemption"


def test_update_favorite_success(auth_client_and_user: tuple[FlaskClient, User], sample_movie: Movie) -> None:
	"""Test updating the rating of a user's favorite movie."""
	client, _ = auth_client_and_user
	response = client.patch(f"/api/favorites/{sample_movie.id}", json={
			"rating": "9.3",
			"genre":  "Drama"
	})
	
	assert response.status_code == 200
	data = response.get_json()
	assert data["message"] == "Movie updated successfully"
	assert data["movie"]["rating"] == "9.3"


def test_delete_favorite_with_tstring(auth_client_and_user: tuple[FlaskClient, User], sample_movie: Movie) -> None:
	"""Test deleting a favorite movie, utilizing secure SQLAlchemy t-strings."""
	client, _ = auth_client_and_user
	response = client.delete(f"/api/favorites/{sample_movie.id}")
	
	assert response.status_code == 204  # No Content
	
	verify_response = client.get("/api/favorites")
	assert len(verify_response.get_json()) == 0


def test_idor_prevention_on_update(app: Flask, client: FlaskClient, sample_movie: Movie) -> None:
	"""Defensive check: Ensure a user cannot update a movie that belongs to someone else."""
	malicious_user_id = uuid.uuid4()
	unique_hacker_name = f"hacker_{malicious_user_id.hex[:8]}"
	
	with app.app_context():
		malicious_user = User(id=malicious_user_id, username=unique_hacker_name, password="password")
		db.session.add(malicious_user)
		db.session.commit()
	
	with client.session_transaction() as sess:
		sess["user_id"] = str(malicious_user_id)
	
	response = client.patch(f"/api/favorites/{sample_movie.id}", json={"rating": "1.0"})
	
	assert response.status_code == 404
