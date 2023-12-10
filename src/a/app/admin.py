#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""admin pannel and apis"""

import typing as t

import flask
from flask_login import current_user, login_user, logout_user  # type: ignore
from werkzeug.wrappers import Response

from .. import const, models, util
from ..routing import Bp

admin: Bp = Bp("admin", __name__)


@admin.get("/")
@util.require_role_route(const.Role.mod)
def index() -> str:
    """index page"""
    return flask.render_template(
        "admin.j2",
        users=models.User.query.all(),
    )


@admin.get("/restore")
@util.require_role_route(const.Role.user)
def restore() -> Response:
    """restore cookies from session"""

    try:
        admin: t.Optional[t.Tuple[str, bool]] = util.get_admin()
        util.clear_admin()

        if admin is None:
            flask.abort(400)

        usr: models.User = models.User.query.filter_by(username=admin[0]).first_or_404()

        logout_user()
        login_user(usr, admin[1])

        flask.flash(f"logged you in as {usr.username!r}", "info")
    except Exception as e:
        flask.flash("failed to restore session", "error")
        flask.current_app.log_exception(e)

    return flask.redirect("/")


@admin.get("/clear")
@util.require_role_route(const.Role.user)
def clear() -> Response:
    """restore cookies from session"""

    util.clear_admin()
    return flask.redirect("/")


@admin.get("/@<string:user>")
@util.require_role_route(const.Role.admin)
def login(user: str) -> Response:
    """login into user account"""

    if user == current_user.username or util.is_admin():  # type: ignore
        return flask.redirect("/")

    usr: models.User = models.User.query.filter_by(username=user).first_or_404()

    if usr.role.value >= current_user.role.value:  # type: ignore
        flask.abort(403)

    util.set_admin()

    logout_user()
    login_user(usr)

    flask.flash(f"logged you in as {user!r}", "info")

    return flask.redirect("/")
