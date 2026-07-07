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
	User model representing registered individuals.
	Uses UUID4 to prevent sequential ID guessing (enumeration).
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
	Director model representing the individual who directed a Movie.
	Extended with birthdate and nationality for richer metadata.
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
	Movie model representing a user's favorite movie fetched from OMDb.
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
