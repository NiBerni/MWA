import logging
from functools import wraps
from typing import Any, Callable

from flask import jsonify

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


def route_error_handler(func: Callable) -> Callable:
	"""
	A decorator to handle exceptions in Flask route functions.
	Logs the exception and returns a JSON response with a 500 status code.
	"""

	@wraps(func)
	def wrapper(*args, **kwargs) -> Any:
		try:
			return func(*args, **kwargs)
		except Exception as e:
			logger.error(f"An error occurred in route {func.__name__}: {e}", exc_info=True)
			response = jsonify({"error": "An unexpected error occurred."})
			response.status_code = 500
			return response

	return wrapper
