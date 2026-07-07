import logging
import time
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
	Decorator to handle exceptions raised by routes.

	:param func: The function to be decorated.
	:return: A new function that wraps the original function and handles any exceptions it may raise.

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
	Wraps a Flask route function to ensure that the request is made by an authenticated user.

	:param func: The Flask route function to be wrapped.
	:return: The wrapped function.
	:raises jsonify: If the session key is missing or malformed.
	:raises jsonify: If there is an error during database lookup.
	"""
	
	@wraps(func)
	def decorated_function(*args: Any, **kwargs: Any) -> Any:
		# 1. Guard Clause: Missing session key
		if "user_id" not in session:
			return jsonify({"error": "Authentication required."}), 401
		
		user_id_raw = session["user_id"]
		
		# 2. Guard Clause: Malformed UUID
		try:
			user_uuid = uuid.UUID(str(user_id_raw))
		except ValueError:
			logger.warning(f"Invalid UUID format in session: {user_id_raw}")
			session.clear()  # FIX: Destroy poisoned session
			return jsonify({"error": "Invalid session format"}), 401
		
		from src.models import User
		
		# 3. Database lookup with safe UUID mapping
		try:
			user = db.session.get(User, user_uuid)
		except (DataError, StatementError) as e:
			logger.error(f"Database error during session validation: {e}")
			session.clear()  # FIX: Destroy poisoned session
			return jsonify({"error": "Invalid session data"}), 401
		
		# 4. Guard Clause: User deleted or not found
		if not user:
			session.clear()  # FIX: Destroy orphaned session cookie
			return jsonify({"error": "Invalid or expired session"}), 401
		
		request.user = user
		return func(*args, **kwargs)
	
	return decorated_function


perf_logger = logging.getLogger("performance")
perf_logger.setLevel(logging.INFO)


def profile_query(func: Callable) -> Callable:
	"""
	Profile a function to measure and log its execution time.

	:param func: The function to be profiled.
	:return: A new function that logs the execution time of the original function.

	"""
	
	@wraps(func)
	def wrapper(*args: Any, **kwargs: Any) -> Any:
		start_time = time.perf_counter()
		result = func(*args, **kwargs)
		execution_time_ms = (time.perf_counter() - start_time) * 1000
		
		if execution_time_ms > 200:
			perf_logger.warning(
					f"[PERFORMANCE WARNING] {func.__name__} took {execution_time_ms:.2f}ms. "
					"Consider adding a database index."
			)
		else:
			perf_logger.info(f"[PROFILER] {func.__name__} executed in {execution_time_ms:.2f}ms.")
		
		return result
	
	return wrapper
