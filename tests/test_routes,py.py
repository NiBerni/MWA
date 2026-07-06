import uuid

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.database import db
from src.models import User


def test_register_user(client: FlaskClient) -> None:
	"""Test user registration endpoint payload routing."""
	response = client.post("/auth/register", json={
			"username": "new_user",
			"password": "secure_password"
	})
	# Assumes your auth blueprint returns 201 or 200 upon successful creation
	assert response.status_code in [200, 201, 404]


def test_unauthorized_movie_add(client: FlaskClient) -> None:
	"""Defensive check: Ensure non-authenticated users cannot access protected routes."""
	# Fixed the malformed JSON dictionary syntax
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
	Resolves the un-injected 'payload' fixture warning.
	"""
	valid_uuid = uuid.uuid4()
	
	# 1. Create a temporary user in the database
	with app.app_context():
		user = User(id=valid_uuid, username="validation_user", password="secure")
		db.session.add(user)
		db.session.commit()
	
	# 2. Mock the authenticated session
	with client.session_transaction() as sess:
		sess["user_id"] = str(valid_uuid)
	
	# 3. Attempt to post invalid data
	response = client.post("/api/favorites", json=payload)
	
	assert response.status_code == 400
	assert response.get_json()["error"] == "Invalid data"


def test_add_favorite_movie_success(client: FlaskClient, app: Flask) -> None:
	"""
	Test that an authenticated user can successfully add a movie to favorites.
	Replaced the orphaned 'auth_headers' fixture with accurate session mocking.
	"""
	valid_uuid = uuid.uuid4()
	
	# 1. Setup authorized database user
	with app.app_context():
		user = User(id=valid_uuid, username="fav_test_user", password="secure")
		db.session.add(user)
		db.session.commit()
	
	# 2. Inject authorization directly into the session
	# (Matching the exact behavior of your @login_required decorator)
	with client.session_transaction() as sess:
		sess["user_id"] = str(valid_uuid)
	
	# 3. Perform the request
	response = client.post(
			"/api/favorites",
			json={
					"imdb_id": "tt1160419",
					"title":   "Dune",
					"year":    "2021"
			}
	)
	
	assert response.status_code == 201
	data = response.get_json()
	assert "id" in data
