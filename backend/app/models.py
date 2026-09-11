from __future__ import annotations

import datetime as dt
import json

from flask_login import UserMixin
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[str]
    created_at: Mapped[dt.datetime] = mapped_column(
        default=lambda: dt.datetime.now(dt.UTC)
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Event(db.Model):
    """Événement unique (une seule édition gérée à la fois, voir §11 hors périmètre V1)."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    date: Mapped[dt.date]
    timezone: Mapped[str] = mapped_column(default="Europe/Paris")

    courses: Mapped[list[Course]] = relationship(
        back_populates="event", cascade="all, delete-orphan", order_by="Course.id"
    )


class Course(db.Model):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    name: Mapped[str]
    color: Mapped[str] = mapped_column(default="#1d4ed8")
    start_time: Mapped[dt.time]

    event: Mapped[Event] = relationship(back_populates="courses")
    troncons: Mapped[list[Troncon]] = relationship(
        back_populates="course", cascade="all, delete-orphan", order_by="Troncon.number"
    )


class Troncon(db.Model):
    __tablename__ = "troncons"
    __table_args__ = (UniqueConstraint("course_id", "number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    number: Mapped[int]
    type: Mapped[str]  # "run" ou "swim"
    filename: Mapped[str]
    length_m: Mapped[float]
    points_json: Mapped[str]  # JSON : [[lat, lon], ...]

    course: Mapped[Course] = relationship(back_populates="troncons")

    @property
    def points(self) -> list[tuple[float, float]]:
        return [tuple(p) for p in json.loads(self.points_json)]

    @points.setter
    def points(self, value: list[tuple[float, float]]) -> None:
        self.points_json = json.dumps(value)
