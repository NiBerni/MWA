from typing import Any, Dict

import requests


class OMDbAPIError(Exception):
	"""
	Custom exception class for errors related to interactions with the OMDb API.

	Attributes:
		message (str): A human-readable error message.
		status_code (int, optional): The HTTP status code associated with the error.

	Methods:
		__init__(self, message: str, status_code: int = None):
			Initialize the exception with a custom message and an optional status code.

		__str__(self) -> str:
			Return the string representation of the exception.

	Example Usage:
		try:
			response = requests.get('http://www.omdbapi.com/api.php?apikey=your_api_key&t=movie_title')
			if response.status_code != 200:
				raise OMDbAPIError("Failed to retrieve movie data", response.status_code)
		except OMDbAPIError as e:
			print(f"OMDb API error: {e}")
	"""
	
	def __init__(self, message: str, status_code: int | None = None) -> None:
		super().__init__(message)
		self.message = message
		self.status_code = status_code
	
	def __str__(self) -> str:
		if self.status_code is not None:
			return f"{self.message} (Status Code: {self.status_code})"
		else:
			return self.message


class OMDbClient:
	"""
	Initialize the client with an API key and an optional timeout.

	:param api_key: The API key required to authenticate requests to the OMDb API.
	:type api_key: str
	:param timeout: The timeout duration for HTTP requests, in seconds. Defaults to 5.
	:type timeout: int

	:raises ValueError: If no API key is provided.
	"""
	
	def __init__(self, api_key: str, timeout: int = 5) -> None:
		"""
		Initialize the client.
		"""
		if not api_key:
			raise ValueError("An API key must be provided to initialize OMDbClient.")
		self.api_key = api_key
		self.base_url = "http://omdbapi.com/"
		self.timeout = timeout
	
	def fetch_movie_by_title(self, title: str) -> Dict[str, Any]:
		"""
		Searches for a movie by its exact Title.
		"""
		params = {
				"apikey": self.api_key,
				"t":      title,
				"type":   "movie"
		}
		try:
			response = requests.get(self.base_url, params=params, timeout=self.timeout)
			response.raise_for_status()
			data = response.json()
			
			if data.get("Response") == "False":
				raise OMDbAPIError(data.get("Error", "Unknown API logical error."))
			return data
		except requests.RequestException as e:
			raise OMDbAPIError(f"Network error occurred while contacting OMDb: {e}") from e
	
	def fetch_movie_by_id(self, imdb_id: str) -> dict[str, Any]:
		"""Searches for a single movie by its exact IMDb ID."""
		params = {
				"apikey": self.api_key,
				"i":      imdb_id,
				"type":   "movie"
		}
		try:
			response = requests.get(self.base_url, params=params, timeout=self.timeout)
			response.raise_for_status()
			data = response.json()
			
			if data.get("Response") == "False":
				raise OMDbAPIError(data.get("Error", "Invalid IMDb ID provided."))
			return data
		except requests.RequestException as e:
			raise OMDbAPIError(f"Network error occurred while contacting OMDb: {e}") from e
		except ValueError as ve:
			raise OMDbAPIError("Received invalid JSON from OMDb.") from ve
	
	def search_movies(self, query: str) -> list[dict[str, Any]]:
		"""Searches for a phrase and returns a list of matching movies."""
		params = {
				"apikey": self.api_key,
				"s":      query,
				"type":   "movie"
		}
		try:
			response = requests.get(self.base_url, params=params, timeout=self.timeout)
			response.raise_for_status()
			data = response.json()
			
			if data.get("Response") == "False":
				raise OMDbAPIError(data.get("Error", "No movies found for that query."))
			
			search_results = data.get("Search", [])
			return search_results
		except requests.RequestException as e:
			raise OMDbAPIError(f"Network error occurred while contacting OMDb: {e}") from e
