#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""a.ari-web.xyz"""

import os
import secrets

import flask


def create_app() -> flask.Flask:
    """create a new flask app"""

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

    from .c import c
    c.init_app(app)

    from .views import views
    app.register_blueprint(views, url_prefix="/")

    from .auth import auth
    app.register_blueprint(auth, url_prefix="/auth")

    return app
