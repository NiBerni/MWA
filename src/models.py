import uuid
from datetime import date
from typing import List, Optional

from cryptography.fernet import Fernet
from flask import current_app
from sqlalchemy import Date, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from src.database import db


class User(db.Model):
	"""
	Represents a user in the system.

	Users have unique usernames and passwords, and can have favorite movies. They also have an associated OMDb API key that is encrypted for storage.

	:ivar id: Unique identifier for the user.
	:type id: uuid.UUID
	:ivar username: Username of the user, must be unique.
	:type username: str
	:ivar password_hash: Hashed version of the user's password.
	:type password_hash: str
	:ivar _omdb_api_key_encrypted: Encrypted OMDb API key for the user.
	:type _omdb_api_key_encrypted: str
	:ivar favorite_movies: List of movies that the user has marked as favorites.
	:type favorite_movies: List[Movie]
	"""
	__tablename__ = "users"
	
	id: Mapped[uuid.UUID] = mapped_column(
			Uuid, primary_key=True, default=uuid.uuid4
	)
	username: Mapped[str] = mapped_column(
			String(64), unique=True, nullable=False
	)
	password_hash: Mapped[str] = mapped_column(
			String(256), nullable=False
	)
	_omdb_api_key_encrypted: Mapped[str] = mapped_column("omdb_api_key", String(256), nullable=False)
	favorite_movies: Mapped[List["Movie"]] = relationship(
			"Movie", back_populates="user", cascade="all, delete-orphan"
	)
	
	@property
	def password(self) -> None:
		"""Preventing reading the plain-text password."""
		raise AttributeError("Password is write-only.")
	
	@password.setter
	def password(self, password: str) -> None:
		"""Hash and store the password when assigned."""
		self.password_hash = generate_password_hash(password)
	
	def check_password(self, password: str) -> bool:
		"""Verifies the password against the stored hash."""
		return check_password_hash(self.password_hash, password)
	
	@property
	def omdb_api_key(self) -> str:
		"""Transparently decrypts the API key for backend usage."""
		fernet = Fernet(current_app.config["ENCRYPTION_KEY"])
		decrypted_bytes = fernet.decrypt(self._omdb_api_key_encrypted.encode("utf-8"))
		return decrypted_bytes.decode("utf-8")
	
	@omdb_api_key.setter
	def omdb_api_key(self, api_key: str) -> None:
		"""Transparently encrypts the API key before DB insertion."""
		fernet = Fernet(current_app.config["ENCRYPTION_KEY"])
		encrypted_bytes = fernet.encrypt(api_key.encode("utf-8"))
		self._omdb_api_key_encrypted = encrypted_bytes.decode("utf-8")


class Director(db.Model):
	"""
	Represent a movie director in the database.

	A ``Director`` object encapsulates information about a film director, including their name,
	birthdate, nationality, and associated movies. This class is part of the ORM model for directors
	in the application's database.

	:ivar id: Unique identifier for the director.
	:type id: int
	:ivar name: Full name of the director.
	:type name: str
	:ivar birthdate: Date of birth of the director.
	:type birthdate: Optional[date]
	:ivar nationality: Nationality of the director.
	:type nationality: str
	:ivar movies: List of ``Movie`` objects associated with this director.
	:type movies: List["Movie"]
	"""
	__tablename__ = "directors"
	
	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	name: Mapped[str] = mapped_column(String(128), nullable=False)
	birthdate: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
	nationality: Mapped[str] = mapped_column(String(64), nullable=True)
	
	movies: Mapped[List["Movie"]] = relationship(
			"Movie", back_populates="director"
	)


class Movie(db.Model):
	"""
	Represent a movie entity in the database.

	This class represents a movie entity and its attributes. It is used to store information about movies in the database, including their title, year, rating, genre, poster URL, user ID, director ID, and relationships with users and directors.

	:ivar id: Unique identifier for the movie.
	:type id: int
	:ivar imdb_id: IMDb ID of the movie.
	:type imdb_id: str
	:ivar title: Title of the movie.
	:type title: str
	:ivar year: Year of release of the movie (optional).
	:type year: str, optional
	:ivar rating: Rating of the movie (optional).
	:type rating: str, optional
	:ivar genre: Genre of the movie (optional).
	:type genre: str, optional
	:ivar poster_url: URL of the movie's poster (optional).
	:type poster_url: str, optional
	:ivar user_id: ID of the user who added the movie to their favorites.
	:type user_id: uuid.UUID
	:ivar director_id: ID of the director associated with the movie (optional).
	:type director_id: int, optional
	:ivar user: Relationship with the User model indicating which user has favorited the movie.
	:type user: User
	:ivar director: Relationship with the Director model indicating which director is associated with the movie (optional).
	:type director: Optional[Director]
	"""
	__tablename__ = "movies"
	
	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	imdb_id: Mapped[str] = mapped_column(String(20), nullable=False)
	title: Mapped[str] = mapped_column(String(255), nullable=False)
	year: Mapped[str] = mapped_column(String(4), nullable=True)
	rating: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
	genre: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
	poster_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
	user_id: Mapped[uuid.UUID] = mapped_column(
			Uuid, ForeignKey("users.id"), nullable=False
	)
	director_id: Mapped[Optional[int]] = mapped_column(
			Integer, ForeignKey("directors.id"), nullable=True
	)
	user: Mapped["User"] = relationship("User", back_populates="favorite_movies")
	director: Mapped[Optional["Director"]] = relationship("Director", back_populates="movies")
