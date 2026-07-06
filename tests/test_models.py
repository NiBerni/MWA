import uuid

from src.database import db
from src.models import Director, Movie, User


def test_user_gets_uuid_primary_key(app, seed_data):
	"""Test that a User gets a valid UUID4 primary key."""
	with app.app_context():
		user = db.session.get(User, seed_data["user_id"])

		assert user.id is not None
		assert isinstance(user.id, uuid.UUID)


def test_user_password_is_hashed(app, seed_data):
	"""Test that a User password is stored as a hash, not plain text."""
	with app.app_context():
		user = db.session.get(User, seed_data["user_id"])

		assert user.password_hash is not None
		assert user.password_hash != seed_data["user_password"]


def test_user_password_checking(app, seed_data):
	"""Test that password verification accepts correct and rejects the wrong password."""
	with app.app_context():
		user = db.session.get(User, seed_data["user_id"])

		assert user.check_password(seed_data["user_password"]) is True
		assert user.check_password("Wr0ngP@ssw0rd!") is False


def test_movie_model_stores_expected_fields(app, seed_data):
	"""Test that the Movie model stores expected field values."""
	with app.app_context():
		movie = db.session.get(Movie, seed_data["movie_id"])

		assert movie.id is not None
		assert movie.imdb_id == "tt1160419"
		assert movie.title == "Dune"
		assert movie.year == "2021"


def test_director_model_stores_expected_fields(app, seed_data):
	"""Test that the Director model stores expected field values."""
	with app.app_context():
		director = db.session.get(Director, seed_data["director_id"])

		assert director.id is not None
		assert director.name == "Denis Villeneuve"
		assert director.birthdate.year == 1970
		assert director.nationality == "Canadian"
		assert director.birthdate.year != 1967


def test_director_can_have_movies(app, seed_data):
	"""Test that a Director can be linked to movies."""
	with app.app_context():
		director = db.session.get(Director, seed_data["director_id"])
		movie = db.session.get(Movie, seed_data["movie_id"])

		assert director is not None
		assert movie is not None

		assert len(director.movies) >= 1
		assert director.movies[0].title == "Dune"
		assert movie.director == director
		assert movie.director.nationality == "Canadian"


def test_movie_can_exist_without_director(app):
	"""Test that a Movie can exist without being linked to a Director."""
	with app.app_context():
		user = User(username="solo_watcher")
		user.password = "S3cureP@ss!"

		movie = Movie(
				imdb_id="tt0111161",
				title="The Shawshank Redemption",
				user=user
		)

		db.session.add(user)
		db.session.add(movie)
		db.session.commit()

		assert movie.id is not None
		assert movie.director is None
