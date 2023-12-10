#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""models"""

import random
import typing as t
from base64 import b85encode, urlsafe_b64encode
from datetime import datetime
from decimal import Decimal
from html import escape as html_escape
from secrets import SystemRandom
from string import digits

import flask
from flask_argon2 import Argon2  # type: ignore
from flask_login import UserMixin  # type: ignore
from flask_sqlalchemy import SQLAlchemy
from readtime import of_markdown as read_time_of_markdown  # type: ignore
from sqlalchemy import DECIMAL, DateTime, Dialect, Enum, TypeDecorator, Unicode
from sqlalchemy.orm import Relationship, relationship

from . import const, md, types, util

db: SQLAlchemy = SQLAlchemy()
argon2: Argon2 = Argon2()
rand: SystemRandom = SystemRandom()


class HugeUInt(TypeDecorator):  # type: ignore
    """huge int type, 0 to (10**64)-1"""

    impl: t.Any = DECIMAL

    def load_dialect_impl(self, dialect: Dialect) -> t.Any:
        """load dialect impl"""
        return dialect.type_descriptor(DECIMAL(65, 0))  # type: ignore

    def process_bind_param(
        self,
        value: t.Optional[t.Any],
        dialect: Dialect,
    ) -> t.Optional[int]:
        """process binding"""

        types.Unused(dialect)

        if value is not None:
            if value < 0 or value > const.HUGEINT_MAX:
                raise ValueError("HugeUInt out of range [0;HUGEINT_MAX]")
            else:
                return int(value)
        else:
            return None

    def process_result_value(
        self,
        value: t.Optional[t.Any],
        dialect: Dialect,
    ) -> t.Optional[Decimal]:
        """process dialect"""
        types.Unused(dialect)
        return Decimal(value) if value is not None else None


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


class BlogPost(db.Model):
    """user blog post"""

    id: str = db.Column(
        db.String(const.ID_LEN),
        primary_key=True,
        nullable=False,
        unique=True,
    )
    slug: str = db.Column(
        db.String(const.BLOG_POST_SLUG_LEN),
        nullable=False,
    )
    title: str = db.Column(
        Unicode(const.BLOG_POST_SLUG_LEN),
        nullable=False,
    )
    keywords: str = db.Column(
        Unicode(const.BLOG_POST_KEYWORDS_LEN),
        nullable=False,
    )
    content: str = db.Column(
        Unicode(const.BLOG_POST_CONTENT_LEN),
        nullable=False,
    )
    description: str = db.Column(
        Unicode(const.BLOG_POST_DESCRIPTION_LEN),
        nullable=False,
    )
    posted: DateTime = db.Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    edited: DateTime = db.Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    username: str = db.Column(
        Unicode(const.USERNAME_LEN),
        db.ForeignKey("blog.username"),
        nullable=False,
    )

    def __init__(
        self,
        title: str,
        keywords: str,
        content: str,
        description: str,
        username: str,
    ) -> None:
        assert len(self.query.filter_by(username=username).all()) <= const.BLOG_POST_MAX, "too many counters"  # type: ignore

        self.id: str = gen_id(self)
        self.set_slug(title)
        self.set_slug(title)
        self.set_title(title)
        self.set_keywords(keywords)
        self.set_content(content)
        self.set_description(description)
        self.username: str = username

    def set_slug(self, title: str) -> None:
        """set slug based off the title"""

        slug: str = md.slugify(title)

        while self.query.filter_by(slug=slug).first() is not None:
            slug = md.slugify(title, prefix=random.randbytes(8).hex())

        self.slug: str = slug

    def set_title(self, title: str) -> None:
        """set title"""

        assert len(title) <= const.BLOG_POST_SLUG_LEN
        self.title: str = title

    def set_keywords(self, keywords: str) -> None:
        """set keywords"""

        assert len(keywords) <= const.BLOG_POST_KEYWORDS_LEN
        self.keywords: str = keywords

    def set_content(self, content: str) -> None:
        """set content"""

        assert len(content) <= const.BLOG_POST_CONTENT_LEN
        self.content: str = content

    def set_description(self, description: str) -> None:
        """set description"""

        assert len(description) <= const.BLOG_POST_DESCRIPTION_LEN
        self.description: str = description

    def read_time(self) -> str:
        """get read time"""
        return read_time_of_markdown(self.content, 150).text  # type: ignore

    def markdown(self) -> str:
        """get markdown"""
        return md.markdown(self.content)

    def delete_post(self) -> bool:
        """delete post"""

        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            flask.current_app.log_exception(e)
            return False


class Blog(db.Model):
    """blog"""

    username: str = db.Column(
        Unicode(const.USERNAME_LEN),
        db.ForeignKey("user.username"),
        nullable=False,
        primary_key=True,
    )
    title: str = db.Column(
        Unicode(const.BLOG_POST_SLUG_LEN),
        nullable=False,
    )
    header: str = db.Column(
        Unicode(const.BLOG_POST_SLUG_LEN),
        nullable=False,
    )
    description: str = db.Column(
        Unicode(const.BLOG_POST_DESCRIPTION_LEN),
        nullable=False,
    )
    keywords: str = db.Column(
        Unicode(const.BLOG_POST_KEYWORDS_LEN),
        nullable=False,
    )
    default_keywords: str = db.Column(
        Unicode(const.BLOG_POST_KEYWORDS_LEN),
        nullable=False,
    )
    primary: str = db.Column(
        db.String(const.BLOG_PRIMARY_LEN),
        nullable=False,
    )
    secondary: str = db.Column(
        db.String(const.BLOG_SECONDARY_LEN),
        nullable=False,
    )
    locale: str = db.Column(
        db.String(const.BLOG_LOCALE_LEN),
        nullable=False,
    )
    comment_url: t.Optional[str] = db.Column(
        db.String(const.BLOG_COMMENT_URL_LEN),
        nullable=True,
    )
    visitor_url: t.Optional[str] = db.Column(
        db.String(const.BLOG_VISITOR_URL_LEN),
        nullable=True,
    )
    style: t.Optional[str] = db.Column(
        db.String(const.BLOG_POST_CONTENT_LEN),
        nullable=True,
    )
    posts: Relationship[BlogPost] = relationship(
        "BlogPost",
        backref="blog",
        lazy="dynamic",
    )

    def __init__(
        self,
        username: str,
        title: str,
        header: str,
        description: str,
        keywords: str,
        default_keywords: str,
        primary: str,
        secondary: str,
        locale: str,
        comment_url: t.Optional[str] = None,
        visitor_url: t.Optional[str] = None,
        style: t.Optional[str] = None,
    ) -> None:
        self.username: str = username
        self.set_title(title)
        self.set_header(header)
        self.set_description(description)
        self.set_keywords(keywords)
        self.set_default_keywords(default_keywords)
        self.set_primary(primary)
        self.set_secondary(secondary)
        self.set_locale(locale)
        self.set_comment_url(comment_url)
        self.set_visitor_url(visitor_url)
        self.set_style(style)

    def set_title(self, title: str) -> None:
        """set title"""

        assert len(title) <= const.BLOG_POST_SLUG_LEN
        self.title: str = title

    def set_header(self, header: str) -> None:
        """set header"""

        assert len(header) <= const.BLOG_POST_SLUG_LEN
        self.header: str = header

    def set_description(self, description: str) -> None:
        """set header"""

        assert len(description) <= const.BLOG_POST_DESCRIPTION_LEN
        self.description: str = description

    def set_keywords(self, keywords: str) -> None:
        """set keywords"""

        assert len(keywords) <= const.BLOG_POST_KEYWORDS_LEN
        self.keywords: str = keywords

    def set_default_keywords(self, default_keywords: str) -> None:
        """set keywords"""

        assert len(default_keywords) <= const.BLOG_POST_KEYWORDS_LEN
        self.default_keywords: str = default_keywords

    def set_primary(self, primary: str) -> None:
        """set primary"""

        assert len(primary) == const.BLOG_PRIMARY_LEN
        self.primary: str = primary

    def set_secondary(self, secondary: str) -> None:
        """set secondary"""

        assert len(secondary) == const.BLOG_SECONDARY_LEN
        self.secondary: str = secondary

    def set_locale(self, locale: str) -> None:
        """set locale"""

        assert len(locale) == const.BLOG_LOCALE_LEN
        assert "_" in locale

        self.locale: str = locale

    def set_visitor_url(self, visitor_url: t.Optional[str]) -> None:
        """set visitor url"""

        assert len(visitor_url or "") <= const.BLOG_VISITOR_URL_LEN
        self.visitor_url: t.Optional[str] = visitor_url

    def set_comment_url(self, comment_url: t.Optional[str]) -> None:
        """set comment url"""

        assert len(comment_url or "") <= const.BLOG_COMMENT_URL_LEN
        self.comment_url: t.Optional[str] = comment_url

    def set_style(self, style: t.Optional[str]) -> None:
        """set style"""

        assert len(style or "") <= const.BLOG_POST_CONTENT_LEN
        self.style: t.Optional[str] = style

    def delete_blog(self) -> bool:
        """delete blog"""

        try:
            for post in self.posts:  # type: ignore
                db.session.delete(post)  # type: ignore

            db.session.delete(self)
            db.session.commit()

            return True
        except Exception as e:
            db.session.rollback()
            flask.current_app.log_exception(e)
            return False


class Counter(db.Model):
    """user counter"""

    id: str = db.Column(
        db.String(const.ID_LEN),
        primary_key=True,
        nullable=False,
        unique=True,
    )
    name: str = db.Column(Unicode(const.NAME_LEN), nullable=False)
    count: int = db.Column(HugeUInt())
    username: str = db.Column(
        Unicode(const.USERNAME_LEN),
        db.ForeignKey("user.username"),
        nullable=False,
    )
    origin: str = db.Column(
        db.String(const.COUNTER_ORIGIN_LEN),
        default=".*",
        nullable=False,
    )
    active: DateTime = db.Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    def __init__(
        self,
        name: str,
        username: str,
        count: int = 0,
        origin: str = ".*",
    ) -> None:
        assert len(self.query.filter_by(username=username).all()) <= const.COUNTERS_LIMIT, "too many counters"  # type: ignore
        assert count <= const.HUGEINT_MAX, "count out of range"

        self.id: str = gen_id(self)
        self.set_name(name)
        self.count: int = count
        self.username: str = username
        self.set_origin(origin)

    def set_name(self, name: str) -> "Counter":
        """set name"""

        assert len(name) <= const.NAME_LEN, "name too long"
        self.name = name
        return self

    def set_origin(self, origin: str) -> "Counter":
        """set origin"""

        origin = origin.splitlines()[0].strip()

        assert len(origin) <= const.COUNTER_ORIGIN_LEN, "name too long"
        self.origin = origin
        return self

    def set_count(self, count: int) -> "Counter":
        """set count"""

        assert count <= const.HUGEINT_MAX, "count out of range"
        self.count = count
        return self

    def to_svg(
        self,
        fill: t.Optional[str] = None,
        font: t.Optional[str] = None,
        size: t.Optional[float] = None,
        baseline: t.Optional[float] = None,
        ratio: t.Optional[float] = None,
        padding: t.Optional[float] = None,
    ) -> str:
        """convert count to svg

        fill -- text colour
        font -- font family
        size -- font size in pixels
        baseline -- baseline offset
        padding -- padding of characters
        ratio -- character ratio"""

        if fill is None:
            fill = "#fff"
        else:
            fill = html_escape(fill)

        if font is None:
            font = "sans-serif"
        else:
            font = html_escape(font)

        size = size or 16

        if baseline is None:
            baseline = 1

        if ratio is None:
            ratio = 1

        if padding is None:
            padding = 1 / ratio

        svg: str = f'<svg xmlns="http://www.w3.org/2000/svg" width="{len(str(self.count)) + padding * ratio}ch" height="{size}" font-size="{size}">'
        svg += f'<text x="50%" y="{size - baseline}" text-anchor="middle" fill="{fill}" font-family="{font}">{self.count}</text>'
        svg += "</svg>"

        return svg

    def json(self) -> t.Dict[str, t.Any]:
        """convert counter to json"""

        return {
            "name": self.name,
            "count": self.count,
        }

    def inc_or_404(self) -> "Counter":
        """increment or 404"""

        if self.count >= const.HUGEINT_MAX:
            return self

        try:
            self.count += 1
            db.session.commit()
        except Exception:
            flask.abort(500)

        return self


class App(db.Model):
    """user app"""

    id: str = db.Column(
        db.String(const.ID_LEN),
        primary_key=True,
        nullable=False,
        unique=True,
    )
    name: str = db.Column(Unicode(const.NAME_LEN), nullable=False)
    public: bool = db.Column(db.Boolean, default=False)
    secret_hash: t.Optional[str] = db.Column(db.String(const.HASH_LEN))
    username: str = db.Column(
        Unicode(const.USERNAME_LEN),
        db.ForeignKey("user.username"),
        nullable=False,
    )
    created: DateTime = db.Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    def __init__(
        self,
        name: str,
        username: str,
        public: bool = False,
        secret: t.Optional[str] = None,
    ) -> None:
        assert len(name) <= const.NAME_LEN, "name too long"
        assert len(self.query.filter_by(username=username).all()) <= const.APPS_LIMIT, "too many apps"  # type: ignore

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
    bio: str = db.Column(Unicode(const.BIO_LEN), nullable=False, default="")
    password_hash: str = db.Column(db.String(const.HASH_LEN), nullable=False)
    pin_hash: str = db.Column(db.String(const.HASH_LEN), nullable=False)
    role: const.Role = db.Column(
        Enum(const.Role), nullable=False, default=const.Role.user
    )
    limited: bool = db.Column(db.Boolean, default=False)
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

    @property
    def blog(self) -> t.Optional[Blog]:
        """get blog"""
        return Blog.query.filter_by(username=self.username).first()  # type: ignore

    @blog.setter
    def blog(self, value: Blog) -> t.Optional[Blog]:
        """get blog"""
        db.session.add(value)

    def __init__(self, username: str, password: str, pin: str) -> None:
        assert self.check_username(username), "invalid username"

        self.username: str = username
        self.bio: str = ""
        self.set_password(password)
        self.set_pin(pin)
        self.role: const.Role = const.Role.user

    def set_password(self, password: str) -> None:
        """set password"""
        assert self.check_password(password), "invalid password"
        self.password_hash: str = hash_data(password)

    def set_pin(self, pin: str) -> None:
        """set pin"""
        assert self.check_pin(pin), "invalid PIN"
        self.pin_hash: str = hash_data(pin)

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

    @staticmethod
    def check_bio(bio: str) -> bool:
        """checks if username is valid"""
        return len(bio) <= const.BIO_LEN

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

            for counter in self.counters:  # type: ignore
                db.session.delete(counter)  # type: ignore

            db.session.delete(self)
            db.session.commit()

            return True
        except Exception as e:
            flask.current_app.log_exception(e)
            db.session.rollback()
            return False
