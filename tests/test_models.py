import uuid

from src.database import db
from src.models import Movie, User


def test_user_gets_uuid_primary_key(app):
	"""Test that a User gets a valid UUID4 primary key."""
	with app.app_context():
		user = User(username="testuser")

		db.session.add(user)
		db.session.commit()
		assert user.id is not None
		assert isinstance(user.id, uuid.UUID)


def test_user_password_is_hashed(app):
	"""Test that a User password is stored as a hash, not plain text."""
	with app.app_context():
		user = User(username="testuser")
		user.set_password("S3cur3P@ssw0rd!")

		assert user.password_hash is not None
		assert user.password_hash != "S3cur3P@ssw0rd!"


def test_user_password_checking(app):
	"""Test that password verification accepts correct and rejects the wrong password."""
	with app.app_context():
		user = User("testuser")
		user.set_password("S3cur3P@ssw0rd!")

		assert user.check_password("S3cur3P@ssw0rd!") is True
		assert user.check_password("Wr0ngP@ssw0rd!") is False


def test_movie_model(app):
	"""Test the Movie model initialization."""
	with app.app_context():
		movie = Movie(
				imdb_id="tt0111161",
				title="The Shawshank Redemption",
				year="1994"
		)
		db.session.add(movie)
		db.session.commit()

		assert movie.id is not None
		assert movie.title == "The Shawshank Redemption"
