from typing import Generator

import pytest
from flask import Flask

from src.app import create_app
from src.database import db


@pytest.fixture
def app() -> Generator[Flask, None, None]:
	"""
	Fixture to create and configure a fresh Flask app instance for each test.
	Utilizes an in-memory SQLite database for fast, isolated testing.
	"""
	app_instance = create_app({
			"TESTING":                 True,
			"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
	})

	with app_instance.app_context():
		# 1. Import all models BEFORE create_all so SQLAlchemy registers them

		# 2. SQLAlchemy automatically resolves the correct creation order
		# based on the ForeignKey constraints.
		db.create_all()

	# Yield the app to the test functions
	yield app_instance

	# 3. Teardown: Clean up the database after the test completes
	with app_instance.app_context():
		db.drop_all()


@pytest.fixture
def client(app: Flask):
	"""Provides a simulated web client to send requests to the application."""
	return app.test_client()
