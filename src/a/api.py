#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""api"""

import typing as t

import flask
from werkzeug.wrappers import Response

from . import const, models
from .routing import Bp

api: Bp = Bp("api", __name__)


@api.get("/")
def index() -> Response:
    """index"""
    return flask.redirect("/")


@api.get("/@<string:username>")
def user(username: str) -> flask.Response:
    """user api"""

    user: t.Optional[models.User] = models.db.session.get(models.User, username)

    if user is None:
        return flask.jsonify([])  # type: ignore

    return flask.jsonify(  # type: ignore
        {
            "user": user.json(),
            "apps": [
                app.json()  # type: ignore
                for app in models.App.query.filter_by(username=username).all()  # type: ignore
            ],
        }
    )


@api.get("/@<string:user>/<string:id>")
def app(user: str, id: str) -> flask.Response:
    """app api"""

    app: t.Optional[models.App] = models.App.query.filter_by(  # type: ignore
        username=user, id=id
    ).first()
    return flask.jsonify([] if app is None else app.json())  # type: ignore


@api.get("/roles")
def roles() -> flask.Response:
    """returns roles"""
    return flask.jsonify(const.Role.json())  # type: ignore
