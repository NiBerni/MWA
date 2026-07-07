import uuid

from cryptography.fernet import Fernet

from src.app import create_app
from src.database import db
from src.decorators import login_required
from src.models import User


def test_login_required_decorator() -> None:
	"""Test that login_required restricts unauthenticated access and securely handles sessions."""
	
	# Create an isolated app instance just for this test so we can safely register a new route
	app = create_app({
			"TESTING":                        True,
			"SQLALCHEMY_DATABASE_URI":        "sqlite:///:memory:",
			"SQLALCHEMY_TRACK_MODIFICATIONS": False,
			"ENCRYPTION_KEY":                 Fernet.generate_key()
	})
	
	@app.route("/protected")
	@login_required
	def protected_route() -> str:
		return "Allowed"
	
	client = app.test_client()
	
	with app.app_context():
		db.create_all()
		
		response = client.get("/protected")
		assert response.status_code == 401
		
		with client.session_transaction() as sess:
			sess["user_id"] = "invalid-test-uuid-string"
		
		response = client.get("/protected")
		assert response.status_code == 401
		
		valid_uuid = uuid.uuid4()
		user = User(
				id=valid_uuid,
				username="test_decorator_user",
				password="secure_password",
				omdb_api_key="fake_key"
		)
		db.session.add(user)
		db.session.commit()
		
		with client.session_transaction() as sess:
			sess["user_id"] = str(valid_uuid)
		
		response = client.get("/protected")
		assert response.status_code == 200
		assert response.data.decode() == "Allowed"
