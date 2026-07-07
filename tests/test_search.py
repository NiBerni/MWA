import uuid

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.database import db
from src.models import Director, Movie, User


@pytest.fixture
def search_test_data(app: Flask, client: FlaskClient) -> tuple[FlaskClient, str]:
	valid_uuid = uuid.uuid4()
	
	with app.app_context():
		user = User(
				id=valid_uuid,
				username="search_user",
				password="secure",
				omdb_api_key="search_fake_key"
		)
		nolan = Director(name="Christopher Nolan")
		villeneuve = Director(name="Denis Villeneuve")
		db.session.add_all([user, nolan, villeneuve])
		db.session.commit()
		
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
		("?min_rating=8.5", 2, ["Inception", "Interstellar"]),
		("?max_rating=8.5", 2, ["Dune", "Prisoners"]),
		("?min_rating=8.0&max_rating=8.1", 2, ["Dune", "Prisoners"]),
		("?author=Nolan", 2, ["Inception", "Interstellar"]),
		("?min_rating=9.0", 0, []),
])
def test_dynamic_movie_search(
		search_test_data: tuple[FlaskClient, str],
		query_string: str,
		expected_count: int,
		expected_titles: list[str]
) -> None:
	client, _ = search_test_data
	response = client.get(f"/api/favorites/search{query_string}")
	
	assert response.status_code == 200
	data = response.get_json()
	assert len(data) == expected_count
	
	returned_titles = [m["title"] for m in data]
	for title in expected_titles:
		assert title in returned_titles


def test_search_sorting(search_test_data: tuple[FlaskClient, str]) -> None:
	client, _ = search_test_data
	response = client.get("/api/favorites/search?sort=rating_asc")
	
	data = response.get_json()
	assert data[0]["title"] == "Dune"
	assert data[-1]["title"] == "Inception"


def test_search_movie_tree_api_failure(client: FlaskClient, auth_headers: dict[str, str]) -> None:
	response = client.get("/api/movies/search?title=Inception", headers=auth_headers)
	assert response.status_code in [401, 500, 502]
