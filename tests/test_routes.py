import uuid
from typing import Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.database import db
from src.models import Movie, User


@pytest.fixture
def sample_movie(app: Flask, auth_client_and_user: tuple[FlaskClient, User]) -> Generator[Movie, None, None]:
	_, user = auth_client_and_user
	with app.app_context():
		movie = Movie(imdb_id="tt0111161", title="The Shawshank Redemption", user_id=user.id)
		db.session.add(movie)
		db.session.commit()
		db.session.refresh(movie)
		yield movie


def test_register_user(client: FlaskClient) -> None:
	unique_username = f"new_user_{uuid.uuid4().hex[:8]}"
	response = client.post("/auth/register", json={
			"username":     unique_username,
			"password":     "secure_password",
			"omdb_api_key": "new_fake_key_123"
	})
	assert response.status_code in [200, 201]


def test_unauthorized_movie_add(client: FlaskClient) -> None:
	response = client.post("/api/favorites", json={"imdb_id": "tt12345", "title": "Test"})
	assert response.status_code == 401


@pytest.mark.parametrize("payload", [
		{},
		{"title": "Dune"},
		{"imdb_id": "tt1160419"},
])
def test_add_favorite_invalid_data(auth_client_and_user: tuple[FlaskClient, User], payload: dict) -> None:
	client, _ = auth_client_and_user
	response = client.post("/api/favorites", json=payload)
	
	assert response.status_code == 400
	assert response.get_json()["error"] in ["Invalid data", "Invalid data payload"]


def test_add_favorite_movie_success(auth_client_and_user: tuple[FlaskClient, User]) -> None:
	client, _ = auth_client_and_user
	response = client.post(
			"/api/favorites",
			json={"imdb_id": "tt1160419", "title": "Dune", "year": "2021"}
	)
	
	assert response.status_code == 201
	assert "id" in response.get_json()


def test_get_favorites(auth_client_and_user: tuple[FlaskClient, User], sample_movie: Movie) -> None:
	client, _ = auth_client_and_user
	response = client.get("/api/favorites")
	
	assert response.status_code == 200
	data = response.get_json()
	assert isinstance(data, list)
	assert len(data) == 1
	assert data[0]["title"] == "The Shawshank Redemption"


def test_update_favorite_success(auth_client_and_user: tuple[FlaskClient, User], sample_movie: Movie) -> None:
	client, _ = auth_client_and_user
	response = client.patch(f"/api/favorites/{sample_movie.id}", json={
			"rating": "9.3",
			"genre":  "Drama"
	})
	
	assert response.status_code == 200
	assert response.get_json()["movie"]["rating"] == "9.3"


def test_update_favorite_not_found(auth_client_and_user: tuple[FlaskClient, User]) -> None:
	client, _ = auth_client_and_user
	fake_id = uuid.uuid4()
	response = client.patch(f"/api/favorites/{fake_id}", json={"rating": "9.3"})
	
	assert response.status_code == 404


def test_delete_favorite_success(auth_client_and_user: tuple[FlaskClient, User], sample_movie: Movie) -> None:
	client, _ = auth_client_and_user
	response = client.delete(f"/api/favorites/{sample_movie.id}")
	
	assert response.status_code == 204
	verify_response = client.get("/api/favorites")
	assert len(verify_response.get_json()) == 0


def test_delete_favorite_not_found(auth_client_and_user: tuple[FlaskClient, User]) -> None:
	client, _ = auth_client_and_user
	fake_id = uuid.uuid4()
	response = client.delete(f"/api/favorites/{fake_id}")
	
	assert response.status_code == 404


def test_idor_prevention_on_update(app: Flask, client: FlaskClient, sample_movie: Movie) -> None:
	malicious_user_id = uuid.uuid4()
	with app.app_context():
		malicious_user = User(
				id=malicious_user_id,
				username="hacker",
				password="password",
				omdb_api_key="hacker_key"
		)
		db.session.add(malicious_user)
		db.session.commit()
	
	with client.session_transaction() as sess:
		sess["user_id"] = str(malicious_user_id)
	
	response = client.patch(f"/api/favorites/{sample_movie.id}", json={"rating": "1.0"})
	assert response.status_code == 404
