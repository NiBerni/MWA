from typing import Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.app import create_app
from src.database import db


@pytest.fixture
def app() -> Generator[Flask, None, None]:
	"""Fixture to create a Flask app instance for testing."""
	app_instance = create_app({
			"TESTING":                 True,
			"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
	})

	with app_instance.app_context():
		db.create_all()

	yield app_instance

	with app_instance.app_context():
		db.session.remove()
		db.drop_all()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
	"""Fixture to create a test client for the Flask app."""
	return app.test_client()
