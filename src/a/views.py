#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""views"""

import typing as t

import flask

from . import models
from .routing import Bp

views: Bp = Bp("views", __name__)


@views.get("/")
def index() -> str:
    """index"""
    return flask.render_template(
        "index.j2",
        users=models.User.query.all(),
    )


@views.get("/tos")
def tos() -> str:
    """terms of service"""
    return flask.render_template("tos.j2")


@views.get("/@<string:username>")
@views.get("/@<string:username>/")
def user(username: str) -> t.Union[str, t.Tuple[str, int]]:
    """index"""

    user: t.Optional[models.User] = models.db.session.get(models.User, username)

    if user is None:
        return flask.render_template("404.j2"), 404

    return flask.render_template(
        "user.j2",
        user=user,
        apps=models.App.query.filter_by(username=username).all(),
    )


@views.get("/git", defaults={"_": ""})
@views.get("/git/", defaults={"_": ""})
@views.get("/git/<path:_>")
def git(_: str):
    """git source"""
    return flask.redirect(
        f"https://ari.lt/lh/us.ari.lt/{flask.request.full_path[4:]}", code=302
    )
