#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""authentication"""

import typing as t

import flask
from flask_ishuman import CaptchaGenerator
from flask_login import login_required, login_user, logout_user  # type: ignore
from werkzeug.wrappers import Response

from . import const, models, util
from .c import c
from .routing import Bp

auth: Bp = Bp("auth", __name__)


@auth.get("/captcha")
def captcha() -> str:
    """returns a captcha as json"""

    new: CaptchaGenerator = c.new()

    return flask.jsonify(  # type: ignore
        [
            new.image(),
            new.audio(),
        ]
    )


@auth.route("/", methods=("POST", "GET"))
def auth_redirect() -> Response:
    """redirect to auth.signin"""
    return flask.redirect(flask.url_for("auth.signin"))


@auth.get("/signout")
@login_required
def signout() -> Response:
    """sign the current user out"""
    logout_user()
    return flask.redirect("/")


@auth.get("/signup")
def signup_page() -> str:
    """signup page"""
    return flask.render_template(
        "signup.j2",
        c=util.jscaptcha(),
        username_len=const.USERNAME_LEN,
        pw_len=const.MAX_PW_LEN,
    )


@auth.get("/signin")
def signin_page() -> str:
    """signin page"""
    return flask.render_template(
        "signin.j2",
        c=util.jscaptcha(),
        username_len=const.USERNAME_LEN,
        pw_len=const.MAX_PW_LEN,
        pin_len=const.PIN_LEN,
    )


@auth.post("/signup")
def signup() -> t.Union[t.Tuple[str, int], Response]:
    """signup logic"""

    username: t.Optional[str] = flask.request.form.get("username")
    password: t.Optional[str] = flask.request.form.get("password")
    code: t.Optional[str] = flask.request.form.get("code")

    if not (username and password and code):
        return util.flash_render("invalid request", "signup.j2"), 400

    if not c.verify(code):
        return util.flash_render("invalid CAPTCHA", "signup.j2"), 403

    pin: str = models.gen_pin()

    try:
        models.db.session.add(models.User(username, password, pin))
        models.db.session.commit()
    except Exception:
        models.db.session.rollback()
        return (
            util.flash_render("username is taken / invalid request", "signup.j2"),
            500,
        )

    return flask.redirect("/")


@auth.post("/signin")
def signin() -> t.Union[t.Tuple[str, int], Response]:
    """login logic"""

    username: t.Optional[str] = flask.request.form.get("username")
    password: t.Optional[str] = flask.request.form.get("password")
    pin: t.Optional[str] = flask.request.form.get("pin")
    code: t.Optional[str] = flask.request.form.get("code")
    user: t.Optional[models.User]

    if not (username and password and pin and code):
        return util.flash_render("invalid request", "signin.j2"), 400

    if not c.verify(code):
        return util.flash_render("invalid CAPTCHA", "signin.j2"), 403

    if (user := models.User.get_by_user(username)) is None:
        return util.flash_render("no such user", "signin.j2"), 404

    if not user.verify_password(password) or not user.verify_pin(pin):
        return util.flash_render("invalid pin and / or password", "signin.j2"), 403

    login_user(user, True)

    return flask.redirect("/")
