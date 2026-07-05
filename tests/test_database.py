from src.database import db


def test_db_initialisation(app):
	"""Test that the database extension is properly registered to the app."""
	with app.app_context():
		assert db.engine is not None


def test_tstring_processor_availability():
	"""Test that the SQLAlchemy 2.1.0b3 TStringProcessor is available
	and ready to process PEP 750 template strings for injection prevention.
	"""
	from sqlalchemy.sql import tstring

	malicious_input = "1 OR 1=1; DROP TABLE users; --"

	safe_query = tstring(t"SELECT * FROM users WHERE username = {malicious_input}")

	complied_string = str(safe_query)
	assert malicious_input not in complied_string
	assert "DROP TABLE" not in complied_string
