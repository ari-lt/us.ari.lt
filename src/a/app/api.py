#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""api"""

import typing as t

import flask
from werkzeug.wrappers import Response

from .. import const, models
from ..routing import Bp

api: Bp = Bp("api", __name__)


@api.after_request  # type: ignore
def after_request(response: flask.Response) -> flask.Response:
    response.headers["Expires"] = "Thu, 01 Jan 1970 00:00:00 GMT"
    response.headers[
        "Cache-Control"
    ] = "max-age=0, no-cache, must-revalidate, proxy-revalidate"
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET"

    return response


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
        username=user,
        id=id,
    ).first()

    if app is None:
        flask.abort(404)

    return flask.jsonify(app.json())  # type: ignore


@api.get("/roles")
def roles() -> flask.Response:
    """returns roles"""
    return flask.jsonify(const.Role.json())  # type: ignore


@api.get("/apps")
def apps() -> flask.Response:
    """returns apps"""
    return flask.jsonify(flask.current_app.config["SUBAPPS"])  # type: ignore
