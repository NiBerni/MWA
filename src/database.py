"""Base class for SQLAlchemy models."""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
	"""Base class for SQLAlchemy models."""
	pass


db = SQLAlchemy(model_class=Base)
