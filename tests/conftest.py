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


@pytest.fixture(scope="session")
def app() -> Generator[Flask, None, None]:
	app_instance = create_app({
			"TESTING":                        True,
			"SQLALCHEMY_DATABASE_URI":        "sqlite:///:memory:",
			"SQLALCHEMY_TRACK_MODIFICATIONS": False,
			"ENCRYPTION_KEY":                 Fernet.generate_key()
	})
	
	with app_instance.app_context():
		db.create_all()
		yield app_instance
		db.drop_all()


@pytest.fixture(scope="session")
def client(app: Flask) -> FlaskClient:
	return app.test_client()


@pytest.fixture(autouse=True)
def clean_database(app: Flask) -> Generator[None, None, None]:
	yield
	
	with app.app_context():
		for table in reversed(db.metadata.sorted_tables):
			db.session.execute(table.delete())
		db.session.commit()


@pytest.fixture
def seed_data(app: Flask) -> dict[str, Any]:
	with app.app_context():
		user = User(
				username="cinephile_master",
				password="S3cur3P@ssw0rd!",
				omdb_api_key="fake_master_key_123"
		)
		director = Director(
				name="Denis Villeneuve",
				nationality="Canadian",
				birthdate=date(1970, 10, 3)
		)
		db.session.add_all([user, director])
		db.session.commit()
		
		movie = Movie(
				imdb_id="tt1160419",
				title="Dune",
				year="2021",
				rating="8.0",
				genre="Sci-Fi, Adventure",
				user_id=user.id,
				director_id=director.id
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
def auth_headers(client: FlaskClient) -> dict[str, str]:
	with client.session_transaction() as sess:
		sess["user_id"] = str(uuid.uuid4())
	return {}


@pytest.fixture
def auth_client_and_user(app: Flask, client: FlaskClient) -> Generator[tuple[FlaskClient, User], None, None]:
	valid_uuid = uuid.uuid4()
	unique_username = f"auth_{valid_uuid.hex[:8]}"
	
	with app.app_context():
		user = User(
				id=valid_uuid,
				username=unique_username,
				password="securepassword123",
				omdb_api_key="fake_omdb_key_123"
		)
		db.session.add(user)
		db.session.commit()
		db.session.refresh(user)
	
	with client.session_transaction() as sess:
		sess["user_id"] = str(valid_uuid)
	
	yield client, user
