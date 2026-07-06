import pytest
import requests
import responses

from src.omdb_client import OMDbAPIError, OMDbClient


@pytest.fixture
def client() -> OMDbClient:
	"""Provides a configured OMDbClient with a fake API key for testing."""
	return OMDbClient(api_key="fake_test_key")


@responses.activate
def test_fetch_movie_by_title_success(client: OMDbClient) -> None:
	responses.add(
			responses.GET,
			"http://omdbapi.com/",
			json={
					"Response": "True",
					"Titel":    "Dune",
					"Year":     "2021",
					"imdbID":   "tt1160419",
					"Director": "Denis Villeneuve"
			},
			status=200
	)

	result = client.fetch_movie_by_title("Dune")

	assert result["Titel"] == "Dune"
	assert result["Year"] == "2021"
	assert result["Response"] == "True"


@responses.activate
def test_fetch_movie_by_title_not_found(client: OMDbClient) -> None:
	"""Test that querying a non-existent movie raises a custom OMDbAPIError."""
	responses.add(
			responses.GET,
			"http://omdbapi.com/",
			json={"Response": "False", "Error": "Movie not found"},
			status=200
	)
	with pytest.raises(OMDbAPIError, match="Movie not found"):
		client.fetch_movie_by_title("SomeFakeMovieThatDoesNotExist")


@responses.activate
def test_fetch_movie_network_failure(client: OMDbClient) -> None:
	"""Test that connection errors are securely caught and wrapped."""
	responses.add(
			responses.GET,
			"http://omdbapi.com/",
			body=requests.exceptions.ConnectionError("Failed to resolve host")
	)
	with pytest.raises(OMDbAPIError, match="Network error occurred"):
		client.fetch_movie_by_title("Dune")


@responses.activate
def test_search_movies_success(client: OMDbClient) -> None:
	"""Test that a broad search correctly parses the nested "Search" array."""
	responses.add(
			responses.GET,
			"http://omdbapi.com/",
			json={
					"Search":       [
							{"Title": "Star Wars: Episode IV - A New Hope", "Year": "1977", "imdb_id": "tt0076759"},
							{
									"Title":  "Star Wars: Episode V - The Empire Strikes Back", "Year": "1980",
									"imdbID": "tt0080684"
							}
					],
					"totalResults": "2",
					"Response":     "True"
			},
			status=200
	)
	results = client.search_movies("Star Wars")

	assert isinstance(results, list)
	assert len(results) == 2
	assert results[0]["Title"] == "Star Wars: Episode IV - A New Hope"
	assert results[1]["imdbID"] == "tt0080684"


@responses.activate
def test_search_movies_not_found(client: OMDbClient) -> None:
	"""Test that an empty search safely raises the custom AOMDbAPIError."""
	responses.add(
			responses.GET,
			"http://omdbapi.com/",
			json={"Response": "False", "Error": "Movie not found!"},
			status=200
	)
	with pytest.raises(OMDbAPIError, match="Movie not found!"):
		client.search_movies("GibberishTitleThatNobodyMade")


@responses.activate
def test_fetch_movie_by_id_success(client: OMDbClient) -> None:
	"""Test that fetching a movie by its unique IMDb ID returns data."""
	responses.add(
			responses.GET,
			"http://omdbapi.com/",
			json={
					"Response":   "True",
					"Title":      "Dune",
					"Year":       "2021",
					"imdbID":     "tt1160419",
					"Director":   "Denis Villeneuve",
					"Genre":      "Sci_Fi, Adventure",
					"imdbRating": "8.0"
			},
			status=200
	)
	result = client.fetch_movie_by_id("tt1160419")

	assert result["Title"] == "Dune"
	assert result["imdbID"] == "tt1160419"
	assert "Genre" in result
