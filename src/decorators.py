import logging
import uuid
from functools import wraps
from typing import Any, Callable

from flask import jsonify, request, session
from sqlalchemy.exc import DataError, StatementError

from src.database import db

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


def route_error_handler(func: Callable) -> Callable:
	"""
	A decorator to handle exceptions in Flask route functions.
	Logs the exception and returns a JSON response with a 500 status code.
	"""
	
	@wraps(func)
	def wrapper(*args: Any, **kwargs: Any) -> Any:
		try:
			return func(*args, **kwargs)
		except Exception as e:
			logger.error(f"An error occurred in route {func.__name__}: {e}", exc_info=True)
			response = jsonify({"error": "An unexpected error occurred."})
			response.status_code = 500
			return response
	
	return wrapper


def login_required(func: Callable) -> Callable:
	"""
	Decorator to protect routes that require an authenticated user.
	Includes defensive checks to prevent database casting errors on malformed session data.
	"""
	
	@wraps(func)
	def decorated_function(*args: Any, **kwargs: Any) -> Any:
		
		# 1. Guard Clause: Missing session key
		if "user_id" not in session:
			return jsonify({"error": "Authentication required."}), 401
		
		user_id_raw = session["user_id"]
		
		# 2. Guard Clause: Malformed UUID
		try:
			# Ensure the session value can be cast to a valid UUID before hitting the ORM
			user_uuid = uuid.UUID(str(user_id_raw))
		except ValueError:
			logger.warning(f"Invalid UUID format in session: {user_id_raw}")
			return jsonify({"error": "Invalid session"}), 401
		
		# 3. Database lookup with safe UUID mapping
		from src.models import User
		try:
			user = db.session.get(User, user_uuid)
		except (DataError, StatementError) as e:
			logger.error(f"Database error during session validation: {e}")
			return jsonify({"error": "Invalid session data"}), 401
		
		# 4. Guard Clause: User deleted or not found
		if not user:
			return jsonify({"error": "Invalid session"}), 401
		
		request.user = user
		
		return func(*args, **kwargs)
	
	return decorated_function
