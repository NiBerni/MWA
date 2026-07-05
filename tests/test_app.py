from flask import Flask

from src.app import create_app
from src.decorators import route_error_handler


def test_app_creation():
	"""Test that the application factory successfully creatres a Flask app"""
	app = create_app()
	assert isinstance(app, Flask)
	assert app.config['TESTING'] is True


def test_route_error_handler(client):
	"""Test that the route_error_handler decorator correctly handles exceptions"""

	app = create_app({"TESTING": True})

	# Define a test route that raises an exception
	@app.route('/faulty-route')
	@route_error_handler
	def error_route():
		raise ValueError("Simulated internal logic error")

	# Override the client for this specific test
	with app.test_client() as test_client:
		response = test_client.get('/faulty-route')
		assert response.status_code == 500
		assert response.is_json
		data = response.get_json()
		assert data['error'] == "An unexpected error occured."
