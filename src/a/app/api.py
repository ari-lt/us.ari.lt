#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""api"""

import typing as t

import flask
from werkzeug.wrappers import Response

from .. import const, models
from ..routing import Bp

api: Bp = Bp("api", __name__).set_api()


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


@api.get("/app/@<string:user>/<string:id>")
def app(user: str, id: str) -> flask.Response:
    """app api"""

    app: models.App = models.App.query.filter_by(  # type: ignore
        username=user,
        id=id,
    ).first_or_404()

    return flask.jsonify(app.json())  # type: ignore


@api.get("/roles")
def roles() -> flask.Response:
    """returns roles"""
    return flask.jsonify(const.Role.json())  # type: ignore


@api.get("/apps")
def apps() -> flask.Response:
    """returns apps"""
    return flask.jsonify(flask.current_app.config["SUBAPPS"])  # type: ignore


@api.get("/counter/@<string:user>/<string:id>")
def counter(user: str, id: str) -> flask.Response:
    """returns apps"""

    counter: models.Counter = models.Counter.query.filter_by(
        username=user,
        id=id,
    ).first_or_404()

    return flask.jsonify(counter.json())  # type: ignore
