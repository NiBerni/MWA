import os
from typing import Any, Mapping, Optional

from dotenv import load_dotenv
from flask import Flask

from src.database import db

load_dotenv()


def create_app(test_config: Optional[Mapping[str, Any]] = None) -> Flask:
	"""
	Create a Flask application instance.

	:param test_config: A dictionary containing configuration overrides for testing. If not provided, the default configuration is used.
	:type test_config: Optional[Mapping[str, Any]]
	:return: The configured Flask application instance.
	:rtype: Flask

	This function initializes and returns a Flask application instance with the necessary configurations and blueprints.
	"""
	app = Flask(__name__, instance_relative_config=True, template_folder="../templates")
	
	# Load default configuration
	app.config.from_mapping(
			SECRET_KEY=os.getenv("FLASK_SECRET_KEY", "dev"),
			SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URI", "sqlite:///moviewebapp.db"),
			SQLALCHEMY_TRACK_MODIFICATIONS=False,
			ENCRYPTION_KEY=os.getenv(
					"ENCRYPTION_KEY",
					"vE7_9-B5XGzP3r8Q2aR1_N9_L0K4Z2W1mJ8vD5xR9Qc="  # Static valid dev key
			)
	)
	
	if test_config is None:
		app.config.from_pyfile("config.py", silent=True)
	else:
		# Load the test config if passed in
		app.config.from_mapping(test_config)
		
		# Ensure tests have a consistent encryption key if not provided in test_config
		if "ENCRYPTION_KEY" not in app.config:
			app.config["ENCRYPTION_KEY"] = os.getenv("ENCRYPTION_KEY", "vE7_9-B5XGzP3r8Q2aR1_N9_L0K4Z2W1mJ8vD5xR9Qc=")
	
	db.init_app(app)
	register_db_cli(app)
	
	from src.routes import api_bp
	app.register_blueprint(api_bp)
	
	from src.auth import auth_bp
	app.register_blueprint(auth_bp)
	
	from src.views import views_bp
	app.register_blueprint(views_bp)
	
	@app.route("/ping")
	def ping() -> dict[str, str]:
		return {"status": "ok"}
	
	register_favicon_route(app)
	
	return app


def register_favicon_route(app: Flask) -> None:
	"""
	Register the favicon route in the Flask application to handle requests for legacy favicon files gracefully.

	:param app: The Flask application instance where the route should be registered.
	:type app: Flask

	:return: None
	"""
	
	@app.route("/favicon.ico")
	def favicon() -> tuple[str, int]:
		"""
		Gracefully catches and handles automated browser requests for a legacy favicon file.

		:return: An empty string and a 204 No Content HTTP status code.
		"""
		return "", 204


def register_db_cli(app: Flask) -> None:
	"""
	Registers custom Flask CLI commands for database management.
	"""
	
	@app.cli.command("init-db")
	def init_db_command() -> None:
		"""Create new database tables based on SQLAlchemy models."""
		with app.app_context():
			# In a production environment, use Alembic migrations.
			# For this MVP, create_all() safely bootstraps the SQLite file.
			db.create_all()
		print("Initialized the database.")
