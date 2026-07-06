from flask import Flask
from flask.testing import FlaskClient

from src.decorators import route_error_handler


def test_app_creation(app: Flask) -> None:
	"""Test that the application factory successfully creates a Flask app"""
	assert isinstance(app, Flask)
	assert app.config["TESTING"] is True


def test_route_error_handler(app: Flask, client: FlaskClient):
	"""Test that the route_error_handler decorator correctly handles exceptions"""
	
	# Define a test route that raises an exception
	@app.route("/faulty-route")
	@route_error_handler
	def error_route():
		raise ValueError("Simulated internal logic error")
	
	response = client.get("/faulty-route")
	
	assert response.status_code == 500
	assert response.is_json
	data = response.get_json()
	assert data is not None
	assert "error" in data
	assert data["error"] == "An unexpected error occurred."
