def test_index_page_loads(client):
	"""
	Ensure the root index page (Login/Register) loads successfully
	for unauthenticated users.
	"""
	response = client.get("/")
	assert response.status_code == 200
	assert b"Login" in response.data or b"Register" in response.data


def test_favorites_dashboard_requires_auth(client):
	"""
	Defensive Guard: Ensure unauthenticated users cannot access the dashboard
	and are redirected to the index/login page.
	"""
	response = client.get("/favorites")
	# Flask-Login or custom decorators typically return 302 Redirect or 401
	assert response.status_code in [302, 401]


def test_favorites_dashboard_authenticated(client, auth_client_and_user):
	"""
	Ensure authenticated users can access their favorites dashboard.
	"""
	user_id = auth_client_and_user  # Using the user UUID from your fixture
	
	# Assuming 'client' is already authenticated via the fixture's session
	response = client.get("/favorites")
	assert response.status_code == 200
	assert b"My Favorites" in response.data
