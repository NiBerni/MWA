import uuid

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import delete

from src.database import db
from src.models import User


# --- 🛡️ DEFENSIVE TDD: Auto-Cleanup Fixture ---
@pytest.fixture(autouse=True)
def clean_database(app: Flask):
	"""Automatically wipes tables clean before and after EVERY test."""
	with app.app_context():
		db.session.execute(delete(User))
		db.session.commit()
	yield
	with app.app_context():
		db.session.execute(delete(User))
		db.session.commit()


@pytest.fixture
def auth_client_and_user(app: Flask, client: FlaskClient) -> tuple[FlaskClient, User]:
	"""Provides a test client with an authenticated session and a uniquely generated User."""
	valid_uuid = uuid.uuid4()
	unique_username = f"auth_{valid_uuid.hex[:8]}"
	
	with app.app_context():
		user = User(id=valid_uuid, username=unique_username, password="secure")
		db.session.add(user)
		db.session.commit()
		db.session.refresh(user)
	
	with client.session_transaction() as sess:
		sess["user_id"] = str(valid_uuid)
	
	yield client, user


def test_register_and_login_flow(client: FlaskClient) -> None:
	"""Verify registration creates a user and login establishes a session."""
	# Register
	reg_response = client.post("/auth/register", json={
			"username": "testuser",
			"password": "securepassword123"
	})
	assert reg_response.status_code == 201
	
	# Login
	login_response = client.post("/auth/login", json={
			"username": "testuser",
			"password": "securepassword123"
	})
	assert login_response.status_code == 200


def test_login_invalid_credentials(client: FlaskClient) -> None:
	"""Verify unauthorized access."""
	response = client.post("/auth/login", json={
			"username": "nonexistent",
			"password": "wrongpassword"
	})
	assert response.status_code == 401
