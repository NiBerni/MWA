from typing import Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.app import create_app


@pytest.fixture
def app() -> Generator[Flask, None, None]:
	"""Fixture to create a Flask app instance for testing."""
	app_instance = create_app({"TESTING": True})
	yield app_instance


@pytest.fixture
def client(app: Flask) -> FlaskClient:
	"""Fixture to create a test client for the Flask app."""
	return app.test_client()
