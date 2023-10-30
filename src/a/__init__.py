#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""a.ari-web.xyz"""

import os
import secrets

import flask


def create_app() -> flask.Flask:
    """create a new flask app"""

    app: flask.Flask = flask.Flask(__name__)

    if not os.path.exists("key"):
        with open("key", "wb") as fp:
            fp.write(secrets.SystemRandom().randbytes(2**14))

    with open("key", "rb") as fp:
        app.config["SECRET_KEY"] = fp.read()

    from .views import views
    app.register_blueprint(views, url_prefix="/")

    return app
