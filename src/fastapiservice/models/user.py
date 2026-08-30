"""User model."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base
from .mixins import IDMixin, TimestampMixin


class User(Base, IDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
