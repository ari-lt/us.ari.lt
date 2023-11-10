#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""models"""

from base64 import b85encode, urlsafe_b64encode
from secrets import SystemRandom
from string import digits
from typing import Optional

from flask_argon2 import Argon2  # type: ignore
from flask_login import UserMixin  # type: ignore
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Relationship, relationship

from . import const

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


class App(db.Model):
    """user app"""

    __tablename__: str = "app"

    id: str = db.Column(db.String, primary_key=True, nullable=False, unique=True)
    name: str = db.Column(db.String(const.APP_NAME_LEN), nullable=False)
    secret: str = db.Column(db.String, nullable=False)
    username: str = db.Column(
        db.String(const.USERNAME_LEN), db.ForeignKey("user.username"), nullable=False
    )

    def __init__(self, name: str, username: str) -> None:
        self.id: str = self.gen_id()
        self.name: str = name
        self.secret: str = gen_secret()
        self.username: str = username

    def gen_id(self) -> str:
        """generate an app id"""

        while True:
            generated_id: str = urlsafe_b64encode(
                rand.randbytes(const.APP_ID_LEN)
            ).decode("ascii")

            try:
                if not self.query.filter_by(id=generated_id).first():
                    return generated_id
            except Exception:
                db.session.rollback()
                continue


class User(UserMixin, db.Model):
    """user"""

    __tablename__: str = "user"

    username: str = db.Column(
        db.String(const.USERNAME_LEN),
        primary_key=True,
        unique=True,
        nullable=False,
    )
    bio: Optional[str] = db.Column(db.String(const.BIO_LEN))
    password_hash: str = db.Column(db.String, nullable=False)
    pin_hash: str = db.Column(db.String, nullable=False)
    admin: bool = db.Column(db.Boolean)
    apps: Relationship[App] = relationship("App", backref="user")

    def __init__(self, username: str, password: str, pin: str) -> None:
        assert username, "no username supplied"
        assert password, "no password supplied"
        assert pin, "no pin supplied"

        assert len(username) <= const.USERNAME_LEN, "username is too long"
        assert len(password) <= const.MAX_PW_LEN, "password is too long"

        self.username: str = username
        self.password_hash: str = hash_data(password)
        self.pin_hash: str = hash_data(pin)
        self.admin: bool = False

    def verify_password(self, password: str) -> bool:
        """is password valid"""
        return hash_verify(password, self.password_hash)

    def verify_pin(self, pin: str) -> bool:
        """is pin valid"""
        return hash_verify(pin, self.pin_hash)

    @staticmethod
    def get_by_user(username: str) -> "Optional[User]":
        """gets user by username"""
        return db.session.get(User, username)

    def get_id(self) -> str:
        """get id"""
        return self.username
