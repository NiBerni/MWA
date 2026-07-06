from typing import Any, Dict

import requests


class OMDbAPIError(Exception):
	"""
	Custom exception raised for any OMDb API-related failures,
	including network timeouts and logical "Not Found" errors.
	"""
	pass


class OMDbClient:
	"""
	Secure wrapper for the OMDb REST API.
	Handles network requests, timeouts, and JSON validation.
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
