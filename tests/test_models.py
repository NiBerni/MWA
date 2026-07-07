import uuid

from src.database import db
from src.models import Director, Movie, User


def test_user_gets_uuid_primary_key(app, seed_data):
	with app.app_context():
		user = db.session.get(User, seed_data["user_id"])
		assert user.id is not None
		assert isinstance(user.id, uuid.UUID)


def test_user_password_is_hashed(app, seed_data):
	with app.app_context():
		user = db.session.get(User, seed_data["user_id"])
		assert user.password_hash is not None
		assert user.password_hash != seed_data["user_password"]


def test_user_password_checking(app, seed_data):
	with app.app_context():
		user = db.session.get(User, seed_data["user_id"])
		assert user.check_password(seed_data["user_password"]) is True
		assert user.check_password("Wr0ngP@ssw0rd!") is False


def test_movie_model_stores_expected_fields(app, seed_data):
	with app.app_context():
		movie = db.session.get(Movie, seed_data["movie_id"])
		assert movie.id is not None
		assert movie.imdb_id == "tt1160419"
		assert movie.title == "Dune"
		assert movie.year == "2021"
		assert movie.rating == "8.0"
		assert "Sci-Fi" in movie.genre
		assert "Horror" not in movie.genre


def test_director_model_stores_expected_fields(app, seed_data):
	with app.app_context():
		director = db.session.get(Director, seed_data["director_id"])
		assert director.id is not None
		assert director.name == "Denis Villeneuve"
		assert director.birthdate.year == 1970
		assert director.nationality == "Canadian"


def test_director_can_have_movies(app, seed_data):
	with app.app_context():
		director = db.session.get(Director, seed_data["director_id"])
		movie = db.session.get(Movie, seed_data["movie_id"])
		
		assert len(director.movies) >= 1
		assert director.movies[0].title == "Dune"
		assert movie.director == director


def test_movie_can_exist_without_director(app):
	with app.app_context():
		user = User(username="solo_watcher", password="S3cureP@ss!", omdb_api_key="fake_solo_key")
		
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


def test_movie_models_poster_url(clean_database) -> None:
	from src.models import Movie
	
	user_id = uuid.uuid4()
	# Dummy user to prevent FK violations in stricter setups (optional depending on DB)
	user = User(id=user_id, username="poster_user", password="pwd", omdb_api_key="poster_key")
	db.session.add(user)
	
	movie = Movie(
			imdb_id="tt123456",
			title="Test Movie",
			user_id=user_id,
			poster_url="https://example.com/poster.jpg"
	)
	db.session.add(movie)
	db.session.commit()
	
	retrieved_movie = db.session.get(Movie, movie.id)
	assert retrieved_movie.poster_url == "https://example.com/poster.jpg"
