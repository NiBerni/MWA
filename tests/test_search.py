import uuid

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import delete

from src.database import db
from src.models import Director, Movie, User


# --- 🛡️ DEFENSIVE TDD: Auto-Cleanup Fixture ---

@pytest.fixture(autouse=True)
def clean_database(app: Flask):
	"""Automatically wipes tables clean before and after EVERY test."""
	with app.app_context():
		db.session.execute(delete(Movie))
		db.session.execute(delete(Director))
		db.session.execute(delete(User))
		db.session.commit()
	yield
	with app.app_context():
		db.session.execute(delete(Movie))
		db.session.execute(delete(Director))
		db.session.execute(delete(User))
		db.session.commit()


@pytest.fixture
def search_test_data(app: Flask, client: FlaskClient) -> tuple[FlaskClient, str]:
	"""Provides a test user with a populated library of movies with IMDb ratings."""
	valid_uuid = uuid.uuid4()
	unique_username = f"search_user_{valid_uuid.hex[:8]}"
	
	with app.app_context():
		user = User(id=valid_uuid, username=unique_username, password="secure")
		db.session.add(user)
		
		nolan = Director(name="Christopher Nolan")
		villeneuve = Director(name="Denis Villeneuve")
		db.session.add_all([nolan, villeneuve])
		db.session.commit()
		
		# Assuming your model stores rating as a string like "8.8" or a float
		m1 = Movie(title="Inception", genre="Sci-Fi", rating="8.8", director_id=nolan.id, user_id=user.id,
		           imdb_id="tt1")
		m2 = Movie(title="Interstellar", genre="Sci-Fi", rating="8.7", director_id=nolan.id, user_id=user.id,
		           imdb_id="tt2")
		m3 = Movie(title="Dune", genre="Sci-Fi", rating="8.0", director_id=villeneuve.id, user_id=user.id,
		           imdb_id="tt3")
		m4 = Movie(title="Prisoners", genre="Drama", rating="8.1", director_id=villeneuve.id, user_id=user.id,
		           imdb_id="tt4")
		
		db.session.add_all([m1, m2, m3, m4])
		db.session.commit()
	
	with client.session_transaction() as sess:
		sess["user_id"] = str(valid_uuid)
	
	return client, str(valid_uuid)


@pytest.mark.parametrize("query_string, expected_count, expected_titles", [
		("?genre=Sci-Fi", 3, ["Inception", "Interstellar", "Dune"]),
		("?min_rating=8.5", 2, ["Inception", "Interstellar"]),  # Boundary test: Min
		("?max_rating=8.5", 2, ["Dune", "Prisoners"]),  # Boundary test: Max
		("?min_rating=8.0&max_rating=8.1", 2, ["Dune", "Prisoners"]),  # Boundary test: Range
		("?author=Nolan", 2, ["Inception", "Interstellar"]),
		("?min_rating=9.0", 0, []),  # No matches
])
def test_dynamic_movie_search(
		search_test_data: tuple[FlaskClient, str],
		query_string: str,
		expected_count: int,
		expected_titles: list[str]
) -> None:
	"""Test the catch-all dynamic search endpoint with boundaries and filters."""
	client, _ = search_test_data
	
	response = client.get(f"/api/favorites/search{query_string}")
	
	assert response.status_code == 200
	data = response.get_json()
	
	assert len(data) == expected_count
	
	returned_titles = [m["title"] for m in data]
	for title in expected_titles:
		assert title in returned_titles


def test_search_sorting(search_test_data: tuple[FlaskClient, str]) -> None:
	"""Test that the API can correctly sort by IMDb rating."""
	client, _ = search_test_data
	
	# Sort Ascending (Lowest First: Dune (8.0), Prisoners (8.1), Interstellar (8.7), Inception (8.8))
	response = client.get("/api/favorites/search?sort=rating_asc")
	data = response.get_json()
	assert data[0]["title"] == "Dune"
	assert data[-1]["title"] == "Inception"
