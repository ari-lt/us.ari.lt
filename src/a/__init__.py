#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""a.ari-web.xyz"""

import os
import secrets
from typing import Optional

import flask
import web_mini
from flask_login import LoginManager  # type: ignore

from .const import USERNAME_LEN


def create_app() -> flask.Flask:
    """create a new flask app"""

    web_mini.compileall()

    app: flask.Flask = flask.Flask(__name__)

    if not os.path.exists("secret.key"):
        with open("secret.key", "wb") as fp:
            fp.write(secrets.SystemRandom().randbytes(2**14))

    with open("secret.key", "rb") as fp:
        app.config["SECRET_KEY"] = fp.read()

    app.config["CAPTCHA_PEPPER_FILE"] = "captcha.key"
    app.config["CAPTCHA_EXPIRY"] = 60 * 10  # 10 minutes

    app.config["SESSION_COOKIE_SAMESITE"] = "None"
    app.config["SESSION_COOKIE_SECURE"] = True

    app.config["REMEMBER_COOKIE_NAME"] = "authorization"
    app.config["REMEMBER_COOKIE_SAMESITE"] = "None"
    app.config["REMEMBER_COOKIE_SECURE"] = True

    app.config["USE_SESSION_FOR_NEXT"] = True

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///main.db"

    from .models import User, argon2, db

    db.init_app(app)

    with app.app_context():
        db.create_all()

    argon2.init_app(app)  # type: ignore

    lm: LoginManager = LoginManager(app)

    lm.login_view = "auth.signin"  # type: ignore
    lm.refresh_view = "auth.signin"  # type: ignore
    lm.session_protection = "strong"  # type: ignore
    lm.login_message = "please sign in"  # type: ignore

    @lm.user_loader  # type: ignore
    def _(username: str) -> Optional[User]:
        """load user by username"""

        if username and len(username) <= USERNAME_LEN:
            return User.get_by_user(username)

    @app.after_request
    def _(response: flask.Response) -> flask.Response:
        """minify resources"""

        if response.content_type == "text/html; charset=utf-8":
            response.set_data(web_mini.html.minify_html(response.get_data(as_text=True)))
        elif response.content_type == "text/css; charset=utf-8":
            response.set_data(web_mini.css.minify_css(response.get_data(as_text=True)))

        return response

    from .c import c

    c.init_app(app)

    from .views import views

    app.register_blueprint(views, url_prefix="/")

    from .auth import auth

    app.register_blueprint(auth, url_prefix="/auth")

    return app
