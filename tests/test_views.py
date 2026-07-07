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
	assert response.status_code in [302, 401]


def test_favorites_dashboard_authenticated(client, auth_client_and_user):
	"""
	Ensure authenticated users without movies are redirected to the add-movie interface.
	"""
	user_id = auth_client_and_user
	
	response = client.get("/favorites")
	
	assert response.status_code == 302
	
	assert "/add-movie" in response.headers["Location"]


from flask.testing import FlaskClient


def test_favicon_route(client: FlaskClient) -> None:
	"""
	Test that the application gracefully handles automatic browser favicon requests
	by returning a 204 No Content status.
	"""
	response = client.get("/favicon.ico")
	
	assert response.status_code == 204
