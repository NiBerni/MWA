import os
from typing import Any, Mapping, Optional

from dotenv import load_dotenv
from flask import Flask

from src.database import db

load_dotenv()


def create_app(test_config: Optional[Mapping[str, Any]] = None) -> Flask:
	"""
	Application factory function to create and configure a Flask app instance.

	:param test_config: Optional dictionary for test configuration.
	:return: Configured Flask app instance.
	"""
	app = Flask(__name__, instance_relative_config=True, template_folder="../templates")
	
	# Load default configuration
	app.config.from_mapping(
			SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "dev"),
			SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URI", "sqlite:///moviewebapp.db"),
			SQLALCHEMY_TRACK_MODIFICATIONS=False,
			ENCRYPTION_KEY=os.environ.get(
					"ENCRYPTION_KEY",
					"vE7_9-B5XGzP3r8Q2aR1_N9_L0K4Z2W1mJ8vD5xR9Qc="  # Static valid dev key
			)
	)
	
	# Load the instance config if it exists when not testing
	if test_config is None:
		app.config.from_pyfile("config.py", silent=True)
	else:
		# Load the test config if passed in
		app.config.from_mapping(test_config)
		
		# Ensure tests have a consistent encryption key if not provided in test_config
		if "ENCRYPTION_KEY" not in app.config:
			app.config["ENCRYPTION_KEY"] = "vE7_9-B5XGzP3r8Q2aR1_N9_L0K4Z2W1mJ8vD5xR9Qc="
	
	db.init_app(app)
	
	from src.routes import api_bp
	app.register_blueprint(api_bp)
	
	from src.auth import auth_bp
	app.register_blueprint(auth_bp)
	
	from src.views import views_bp
	app.register_blueprint(views_bp)
	
	@app.route("/ping")
	def ping() -> dict[str, str]:
		return {"status": "ok"}
	
	@app.route("/favicon.ico")
	def favicon() -> tuple[str, int]:
		"""
		Gracefully catches and handles automated browser requests for a legacy favicon file.

		:return: An empty string and a 204 No Content HTTP status code.
		"""
		return "", 204
	
	return app
