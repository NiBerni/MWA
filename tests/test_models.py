import uuid
from datetime import date

from src.database import db
from src.models import Director, Movie, User

TEST_PASSWORD = "S3cur3P@ssw0rd!"


def create_user(username: str = "testuser") -> User:
	"""Create and stage a test user."""
	user = User(username=username)
	user.password = TEST_PASSWORD
	db.session.add(user)
	return user


def create_director(
		name: str = "Denis Villeneuve",
		nationality: str = "Canadian",
		birthdate: date | None = None
) -> Director:
	"""Create and stage a test director."""
	director = Director(
			name=name,
			nationality=nationality,
			birthdate=birthdate
	)
	db.session.add(director)
	return director


def create_movie(
		imdb_id: str = "tt0111161",
		title: str = "The Shawshank Redemption",
		user: User | None = None,
		director: Director | None = None,
		year: str | None = None
) -> Movie:
	"""Create and stage a test movie."""
	if user is None:
		user = create_user()

	movie = Movie(
			imdb_id=imdb_id,
			title=title,
			year=year,
			user=user,
			director=director
	)
	db.session.add(movie)
	return movie


def test_user_gets_uuid_primary_key(app):
	"""Test that a User gets a valid UUID4 primary key."""
	with app.app_context():
		user = create_user()

		db.session.commit()

		assert user.id is not None
		assert isinstance(user.id, uuid.UUID)


def test_user_password_is_hashed(app):
	"""Test that a User password is stored as a hash, not plain text."""
	with app.app_context():
		user = User(username="testuser")
		user.password = TEST_PASSWORD

		assert user.password_hash is not None
		assert user.password_hash != TEST_PASSWORD


def test_user_password_checking(app):
	"""Test that password verification accepts correct and rejects the wrong password."""
	with app.app_context():
		user = User(username="testuser")
		user.password = TEST_PASSWORD

		assert user.check_password(TEST_PASSWORD) is True
		assert user.check_password("Wr0ngP@ssw0rd!") is False


def test_movie_model_stores_expected_fields(app):
	"""Test that the Movie model stores expected field values."""
	with app.app_context():
		movie = create_movie(
				imdb_id="tt0111161",
				title="The Shawshank Redemption",
				year="1994"
		)

		db.session.commit()

		assert movie.id is not None
		assert movie.imdb_id == "tt0111161"
		assert movie.title == "The Shawshank Redemption"
		assert movie.year == "1994"


def test_director_model_stores_expected_fields(app):
	"""Test that the Director model stores expected field values."""
	with app.app_context():
		director = create_director(
				name="Christopher Nolan",
				birthdate=date(1970, 7, 30),
				nationality="British-American"
		)

		db.session.commit()

		assert director.id is not None
		assert director.name == "Christopher Nolan"
		assert director.birthdate.year == 1970
		assert director.nationality == "British-American"


def test_director_can_have_movies(app):
	"""Test that a Director can be linked to movies."""
	with app.app_context():
		user = create_user(username="cinephile_master")
		director = create_director(
				name="Denis Villeneuve",
				nationality="Canadian"
		)

		movie = create_movie(
				imdb_id="tt1160419",
				title="Dune",
				user=user,
				director=director
		)

		db.session.commit()

		assert len(director.movies) == 1
		assert director.movies[0].title == "Dune"
		assert movie.director == director
		assert movie.director.nationality == "Canadian"


def test_movie_can_exist_without_director(app):
	"""Test that a Movie can exist without being linked to a Director."""
	with app.app_context():
		user = create_user(username="cinephile_master")

		movie = create_movie(
				imdb_id="tt0111161",
				title="The Shawshank Redemption",
				user=user
		)

		db.session.commit()

		assert movie.id is not None
		assert movie.director is None
