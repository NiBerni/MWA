from flask.testing import FlaskClient

from src.database import db
from src.models import User


def test_register_and_login_flow(client: FlaskClient) -> None:
	reg_response = client.post("/auth/register", json={
			"username":     "testuser",
			"password":     "securepassword123",
			"omdb_api_key": "fake_omdb_key_123"
	})
	assert reg_response.status_code == 201
	
	login_response = client.post("/auth/login", json={
			"username": "testuser",
			"password": "securepassword123"
	})
	assert login_response.status_code == 200


def test_register_duplicate_username_fails(client: FlaskClient) -> None:
	payload = {"username": "duplicate_user", "password": "secure"}
	client.post("/auth/register", json=payload)
	
	duplicate_response = client.post("/auth/register", json=payload)
	assert duplicate_response.status_code in [400, 409]


def test_update_user_profile(auth_client_and_user: tuple[FlaskClient, User]) -> None:
	client, user = auth_client_and_user
	
	update_response = client.patch("/auth/profile", json={
			"password":     "new_secure_password",
			"omdb_api_key": "new_fake_omdb_key"
	})
	assert update_response.status_code == 200
	
	with client.application.app_context():
		updated_user = db.session.get(User, user.id)
		assert updated_user.check_password("new_secure_password") is True
		assert updated_user.omdb_api_key == "new_fake_omdb_key"


def test_delete_user_profile(auth_client_and_user: tuple[FlaskClient, User]) -> None:
	client, user = auth_client_and_user
	user_id = user.id
	
	delete_response = client.delete("/auth/profile")
	assert delete_response.status_code == 204
	
	with client.application.app_context():
		deleted_user = db.session.get(User, user_id)
		assert deleted_user is None


def test_logout_flow(auth_client_and_user: tuple[FlaskClient, User]) -> None:
	client, _ = auth_client_and_user
	
	response = client.post("/auth/logout")
	assert response.status_code == 200
	assert response.get_json()["message"] == "Logged out successfully"
	
	protected_response = client.get("/api/favorites")
	assert protected_response.status_code == 401


def test_orphaned_session_is_cleared(client: FlaskClient) -> None:
	with client.session_transaction() as sess:
		sess["user_id"] = "00000000-0000-0000-0000-000000000000"
	
	response = client.get("/api/favorites")
	assert response.status_code == 401
	
	with client.session_transaction() as sess:
		assert "user_id" not in sess
