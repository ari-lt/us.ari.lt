#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""models"""

import typing as t
from base64 import b85encode, urlsafe_b64encode
from datetime import datetime
from secrets import SystemRandom
from string import digits

from flask_argon2 import Argon2  # type: ignore
from flask_login import UserMixin  # type: ignore
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime, Enum, Unicode
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Relationship, relationship

from . import const, util

db: SQLAlchemy = SQLAlchemy()
argon2: Argon2 = Argon2()
rand: SystemRandom = SystemRandom()


def gen_pin() -> str:
    """generate a pin"""
    return "".join(rand.choices(digits, k=const.PIN_LEN))


def gen_secret() -> str:
    """generate a secret"""
    return b85encode(rand.randbytes(const.APP_SECRET_LEN)).decode()


def hash_data(data: str) -> str:
    """hash data"""
    return argon2.generate_password_hash(data)  # type: ignore


def hash_verify(data: str, h: str) -> bool:
    """hash data"""
    return argon2.check_password_hash(h, data)  # type: ignore


def gen_id(model: t.Any) -> str:  # type: ignore
    """generate an id"""

    while True:
        generated_id: str = urlsafe_b64encode(rand.randbytes(const.ID_LEN)).decode(
            "ascii"
        )[: const.ID_LEN]

        try:
            if not model.query.filter_by(id=generated_id).first():  # type: ignore
                return generated_id
        except Exception:
            continue


class Counter(db.Model):
    """user counter"""

    id: str = db.Column(
        db.String(const.ID_LEN),
        primary_key=True,
        nullable=False,
        unique=True,
    )
    name: str = db.Column(Unicode(const.NAME_LEN), nullable=False)
    count: int = db.Column(mysql.INTEGER(unsigned=True))
    username: str = db.Column(
        Unicode(const.USERNAME_LEN),
        db.ForeignKey("user.username"),
        nullable=False,
    )

    def __init__(self, name: str, username: str) -> None:
        self.id: str = gen_id(self)
        self.name: str = name
        self.username: str = username

    def to_svg(self) -> str:
        """convert count to svg"""

        svg_width: int = len(str(self.count)) * 14

        svg: str = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" height="20">'
        )
        svg += f'<text x="{svg_width / 2}" y="20" font-size="20px" fill="white" text-anchor="middle" font-family="sans-serif">{self.count}</text>'
        svg += "</svg>"

        return svg

    def json(self) -> t.Dict[str, t.Any]:
        """convert counter to json"""

        return {
            "name": self.name,
            "count": self.count,
        }


class App(db.Model):
    """user app"""

    id: str = db.Column(
        db.String(const.ID_LEN),
        primary_key=True,
        nullable=False,
        unique=True,
    )
    name: str = db.Column(Unicode(const.NAME_LEN), nullable=False)
    public: bool = db.Column(db.Boolean)
    secret_hash: t.Optional[str] = db.Column(db.String(const.HASH_LEN))
    username: str = db.Column(
        Unicode(const.USERNAME_LEN),
        db.ForeignKey("user.username"),
        nullable=False,
    )

    def __init__(
        self,
        name: str,
        username: str,
        public: bool = False,
        secret: t.Optional[str] = None,
    ) -> None:
        self.id: str = gen_id(self)
        self.name: str = name
        self.public: bool = public

        if secret is None:
            self.secret_hash: t.Optional[str] = None
        else:
            self.set_secret(secret)

        self.username: str = username

    def verify_secret(self, secret: str) -> bool:
        """is secret valid"""
        return self.secret_hash is not None and hash_verify(secret, self.secret_hash)

    def set_secret(self, secret: t.Optional[str] = None) -> None:
        """set secret"""
        self.secret_hash: t.Optional[str] = (
            None
            if self.public
            else hash_data(gen_secret() if secret is None else secret)
        )

    def json(self) -> t.Dict[str, t.Any]:
        """return app as json"""

        return {
            "id": self.id,
            "name": self.name,
            "public": self.public,
        }


class User(UserMixin, db.Model):
    """user"""

    username: str = db.Column(
        db.String(const.USERNAME_LEN),
        primary_key=True,
        unique=True,
        nullable=False,
    )
    bio: str = db.Column(Unicode(const.BIO_LEN), nullable=False)
    password_hash: str = db.Column(db.String(const.HASH_LEN), nullable=False)
    pin_hash: str = db.Column(db.String(const.HASH_LEN), nullable=False)
    role: const.Role = db.Column(Enum(const.Role), nullable=False)
    limited: bool = db.Column(db.Boolean)
    joined: DateTime = db.Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    apps: Relationship[App] = relationship(
        "App",
        backref="user",
        lazy="dynamic",
    )
    counters: Relationship[Counter] = relationship(
        "Counter",
        backref="user",
        lazy="dynamic",
    )

    def __init__(self, username: str, password: str, pin: str) -> None:
        assert self.check_pin(pin), "invalid PIN"
        assert self.check_username(username), "invalid username"
        assert self.check_password(password), "invalid password"

        self.username: str = username
        self.bio: str = ""
        self.set_password(password)
        self.pin_hash: str = hash_data(pin)
        self.role: const.Role = const.Role.user

    def set_password(self, password: str) -> None:
        """set password"""
        self.password_hash: str = hash_data(password)

    @staticmethod
    def check_username(username: str) -> bool:
        """checks if username is valid"""
        return (
            bool(username)
            and len(username) <= const.USERNAME_LEN
            and util.validate_username(username)
        )

    @staticmethod
    def check_password(password: str) -> bool:
        """checks if username is valid"""
        return bool(password)

    @staticmethod
    def check_pin(pin: str) -> bool:
        """checks if username is valid"""
        return bool(pin) and len(pin) == const.PIN_LEN

    def verify_password(self, password: str) -> bool:
        """is password valid"""
        return hash_verify(password, self.password_hash)

    def verify_pin(self, pin: str) -> bool:
        """is pin valid"""
        return hash_verify(pin, self.pin_hash)

    @staticmethod
    def get_by_user(username: str) -> "t.Optional[User]":
        """gets user by username"""
        return db.session.get(User, username)

    def get_id(self) -> str:
        """get id"""
        return self.username

    def json(self) -> t.Dict[str, t.Any]:
        """return user as json"""

        return {
            "bio": self.bio,
            "role": self.role.value,
        }

    def delete_user(self) -> bool:
        """delete this user, returns true if success"""

        try:
            for app in self.apps:  # type: ignore
                db.session.delete(app)  # type: ignore

            db.session.delete(self)
            db.session.commit()

            return True
        except Exception:
            db.session.rollback()
            return False
