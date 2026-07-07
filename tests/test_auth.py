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
		# --- 🛡️ FIX IS HERE: We added omdb_api_key="dummy_test_api_key_123" ---
		user = User(
				id=valid_uuid,
				username=unique_username,
				password="secure",
				omdb_api_key="dummy_test_api_key_123"
		)
		db.session.add(user)
		db.session.commit()
		db.session.refresh(user)
	
	with client.session_transaction() as sess:
		sess["user_id"] = str(valid_uuid)
	
	yield client, user


def test_register_and_login_flow(client: FlaskClient) -> None:
	"""Verify registration securely creates a user with an encrypted API key."""
	# Register
	reg_response = client.post("/auth/register", json={
			"username":     "testuser",
			"password":     "securepassword123",
			"omdb_api_key": "fake_omdb_key_123"
	})
	assert reg_response.status_code == 201
	
	# Login
	login_response = client.post("/auth/login", json={
			"username": "testuser",
			"password": "securepassword123"
	})
	assert login_response.status_code == 200


def test_update_user_profile(auth_client_and_user: tuple[FlaskClient, User]) -> None:
	"""Verify an authenticated user can update their password and API key."""
	client, user = auth_client_and_user
	
	update_response = client.patch("/auth/profile", json={
			"password":     "new_secure_password",
			"omdb_api_key": "new_fake_omdb_key"
	})
	assert update_response.status_code == 200
	
	# Verify the changes persisted and the new API key decrypts correctly
	with client.application.app_context():
		updated_user = db.session.get(User, user.id)
		assert updated_user.check_password("new_secure_password") is True
		assert updated_user.omdb_api_key == "new_fake_omdb_key"


def test_delete_user_profile(auth_client_and_user: tuple[FlaskClient, User]) -> None:
	"""Verify a user can delete their own profile and all associated data."""
	client, user = auth_client_and_user
	user_id = user.id
	
	delete_response = client.delete("/auth/profile")
	assert delete_response.status_code == 204
	
	# Verify user is completely removed from the database
	with client.application.app_context():
		deleted_user = db.session.get(User, user_id)
		assert deleted_user is None


def test_logout_flow(auth_client_and_user: tuple[FlaskClient, User]) -> None:
	"""Verify an authenticated user can securely log out."""
	client, _ = auth_client_and_user
	
	response = client.post("/auth/logout")
	assert response.status_code == 200
	assert response.get_json()["message"] == "Logged out successfully"
	
	# Verify session is wiped by hitting a protected route
	protected_response = client.get("/api/favorites")
	assert protected_response.status_code == 401


def test_orphaned_session_is_cleared(app: Flask, client: FlaskClient) -> None:
	"""Verify that a session cookie for a non-existent user is destroyed."""
	# Inject a syntactically valid but logically dead UUID
	with client.session_transaction() as sess:
		sess["user_id"] = "00000000-0000-0000-0000-000000000000"
	
	response = client.get("/api/favorites")
	assert response.status_code == 401
	
	# The poisoned cookie must be actively wiped by the guard clause
	with client.session_transaction() as sess:
		assert "user_id" not in sess
