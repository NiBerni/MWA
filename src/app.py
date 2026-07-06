from typing import Any, Mapping, Optional

from flask import Flask

from src.database import db


def create_app(test_config: Optional[Mapping[str, Any]] = None) -> Flask:
	"""
	Application factory function to create and configure a Flask app instance.

	:param test_config: Optional dictionary for test configuration.
	:return: Configured Flask app instance.
	"""
	app = Flask(__name__, instance_relative_config=True)
	
	# Load default configuration
	app.config.from_mapping(
			SECRET_KEY='dev',
			SQLALCHEMY_DATABASE_URI="sqlite:///moviewebapp.db",
			SQLALCHEMY_TRACK_MODIFICATIONS=False,
	)
	# Load the instance config if it exists when not testing
	if test_config is None:
		app.config.from_pyfile("config.py", silent=True)
	else:
		# Load the test config if passed in
		app.config.from_mapping(test_config)
	db.init_app(app)
	
	from src.routes import api_bp
	app.register_blueprint(api_bp)
	
	from src.auth import auth_bp
	app.register_blueprint(auth_bp)
	
	@app.route("/ping")
	def ping() -> dict[str, str]:
		return {"status": "ok"}
	
	return app
