def test_register_and_login_flow(client, clean_database):
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
	fav_response = client.get("/api/favorites")
	assert fav_response.status_code == 200


def test_login_invalid_credentials(client, clean_database):
	"""Verify unauthorized access."""
	response = client.post("/auth/login", json={
			"username": "nonexistent",
			"password": "wrongpassword"
	})
	assert response.status_code == 401
