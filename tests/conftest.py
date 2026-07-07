import uuid
from datetime import date
from typing import Any, Generator

import pytest
from cryptography.fernet import Fernet
from flask import Flask
from flask.testing import FlaskClient

from src.app import create_app
from src.database import db
from src.models import Director, Movie, User


@pytest.fixture(scope="module")
def app() -> Generator[Flask, None, None]:
	"""
	Fixture to create and configure a fresh Flask app instance for the test module.
	Uses an in-memory SQLite database for fast, isolated testing.
	"""
	# 1. Pass ALL configurations directly into the factory dictionary
	app_instance = create_app({
			"TESTING":                        True,
			"SQLALCHEMY_DATABASE_URI":        "sqlite:///:memory:",
			"SQLALCHEMY_TRACK_MODIFICATIONS": False,
			"ENCRYPTION_KEY":                 Fernet.generate_key()  # Automatically injected on creation
	})
	
	# 2. Use the correct variable name (app_instance) for the context
	with app_instance.app_context():
		db.create_all()
		# Yield the app to the test functions
		yield app_instance
		db.drop_all()


@pytest.fixture(scope="module")
def client(app: Flask):
	"""Provides a simulated web client to send requests to the application."""
	return app.test_client()


# tests/conftest.py

@pytest.fixture
def clean_database(app: Flask) -> Generator[None, None, None]:
	"""
	Cleans all database tables after each test.
	Uses sorted_tables to respect foreign key constraints during deletion.
	"""
	yield  # Test runs here
	
	with app.app_context():
		# Iterate over tables in reverse order to respect foreign key constraints
		for table in reversed(db.metadata.sorted_tables):
			db.session.execute(table.delete())
		db.session.commit()


@pytest.fixture(scope="module")
def seed_data(app: Flask) -> dict[str, Any]:
	"""
	Populates the database with initial, reusable data.
	Returns a dictionary of identifiers to avoid DetachedInstanceErrors
	when accessing abjects outside the app context.
	"""
	with app.app_context():
		user = User(username="cinephile_master")
		user.password = "S3cur3P@ssw0rd!"
		db.session.add(user)
		
		director = Director(
				name="Denis Villeneuve",
				nationality="Canadian",
				birthdate=date(1970, 10, 3)
		)
		db.session.add(director)
		
		movie = Movie(
				imdb_id="tt1160419",
				title="Dune",
				year="2021",
				rating="8.0",
				genre="Sci-Fi, Adventure",
				user=user,
				director=director
		)
		db.session.add(movie)
		db.session.commit()
		
		return {
				"user_id":       user.id,
				"user_username": user.username,
				"user_password": "S3cur3P@ssw0rd!",
				"director_id":   director.id,
				"movie_id":      movie.id,
				"movie_title":   movie.title
		}


@pytest.fixture
def auth_headers(client: FlaskClient, seed_data: dict[str, Any]) -> dict[Any, Any]:
	"""Logs in and returns headers for authenticated requests."""
	with client.session_transaction() as sess:
		sess["user_id"] = uuid.uuid4()
	return {}


@pytest.fixture
def auth_client_and_user(app: Flask, client: FlaskClient) -> tuple[FlaskClient, User]:
	"""Provides a test client with an authenticated session and a uniquely generated User."""
	valid_uuid = uuid.uuid4()
	unique_username = f"auth_{valid_uuid.hex[:8]}"
	
	with app.app_context():
		user = User(
				id=valid_uuid,
				username=unique_username,
				password="securepassword123",
				_omdb_api_key="fake_omdb_key_123"
		)
		db.session.add(user)
		db.session.commit()
		db.session.refresh(user)
	
	with client.session_transaction() as sess:
		sess["user_id"] = str(valid_uuid)
	
	yield client, user
