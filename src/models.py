import uuid
from typing import List

from sqlalchemy import ForeignKey, Integer, String, Uuid
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
	favorite_movies: Mapped[List["Movie"]] = relationship(
			"Movie", back_populates="user", cascade="all, delete-orphan"
	)

	def set_password(self, password: str) -> None:
		"""Hashes the password securely using werkzeug."""
		self.password_hash = generate_password_hash(password)

	def check_password(self, password: str) -> bool:
		"""Verifies the password against the stored hash."""
		return check_password_hash(self.password_hash, password)


class Movie(db.Model):
	"""
	Movie model representing a user's favorite movie fetched from OMDb.
	"""
	__tablename__ = "movies"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	imdb_id: Mapped[str] = mapped_column(String(20), nullable=False)
	title: Mapped[str] = mapped_column(String(255), nullable=False)
	year: Mapped[str] = mapped_column(String(4), nullable=True)
	user_id: Mapped[uuid.UUID] = mapped_column(
			Uuid, ForeignKey("users.id"), nullable=False
	)
	user: Mapped["User"] = relationship("User", back_populates="favorite_movies")
