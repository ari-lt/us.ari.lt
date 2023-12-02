#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""admin pannel and apis"""

import typing as t

import flask
from flask_login import current_user  # type: ignore
from werkzeug.wrappers import Response

from .. import const, models, util
from ..routing import Bp

admin: Bp = Bp("admin", __name__).set_role(const.Role.mod)


@admin.get("/")
@util.require_role_route(const.Role.mod)
def index() -> str:
    """index page"""
    return flask.render_template(
        "admin.j2",
        users=models.User.query.all(),
    )


@admin.get("/manage/@<string:user>")
@util.require_role_route(const.Role.mod)
def manage(user: str) -> t.Union[str, Response]:
    """manage user"""

    usr: t.Optional[models.User]

    if user == current_user.username:  # type: ignore
        return flask.redirect(flask.url_for("auth.manage"))

    if (usr := models.User.query.filter_by(username=user).first()) is None:  # type: ignore
        flask.abort(404)

    return flask.render_template(
        "manage.j2",
        current_user=usr,
        admin=current_user,
        c=util.jscaptcha(),
    )


@admin.post("/manage/@<string:user>")
@util.require_role_route(const.Role.mod)
@util.captcha
def manage_user(user: str) -> Response:
    """manage user"""

    usr: t.Optional[models.User]

    if user == current_user.username:  # type: ignore
        flask.abort(400)

    if (usr := models.User.query.filter_by(username=user).first()) is None:  # type: ignore
        flask.abort(404)

    password: t.Optional[str] = flask.request.form.get("password")
    role: t.Optional[str] = flask.request.form.get("role")
    bio: t.Optional[str] = flask.request.form.get("bio")

    if util.require_role(const.Role.admin) and password:
        usr.set_password(password)  # type: ignore

    if role:
        try:
            usr.role = const.Role(int(role))
        except ValueError:
            flask.flash("failed to update the role : invalid value")

    if bio is not None:
        usr.bio = bio

    try:
        models.db.session.commit()
        flask.flash(f"user {user!r} updated", "info")
    except Exception:
        flask.flash(f"failed to update user {user!r}", "error")

    return flask.redirect(flask.url_for("admin.index"))


@admin.get("/delete/@<string:user>")
@util.require_role_route(const.Role.admin)
def delete(user: str) -> t.Union[str, Response]:
    """delete a user"""

    usr: t.Optional[models.User]

    if user == current_user.username:  # type: ignore
        return flask.redirect(flask.url_for("auth.delete"))

    if (usr := models.User.query.filter_by(username=user).first()) is None:  # type: ignore
        flask.abort(404)

    return flask.render_template(
        "delete.j2",
        current_user=usr,
        c=util.jscaptcha(),
    )


@admin.post("/delete/@<string:user>")
@util.require_role_route(const.Role.admin)
@util.captcha
def delete_user(user: str) -> t.Union[str, Response]:
    """delete a user"""

    sure: t.Optional[str] = flask.request.form.get("sure")
    usr: t.Optional[models.User]

    if sure != "on":
        flask.flash("account not deleted", "info")
        return flask.redirect(flask.url_for("admin.index"))

    if (usr := models.User.query.filter_by(username=user).first()) is None:  # type: ignore
        flask.abort(404)

    if not usr.delete_user():  # type: ignore
        flask.flash("failed to delete account", "error")
        flask.abort(500)

    flask.flash(f"account {user!r} deleted", "info")

    return flask.redirect("/")
