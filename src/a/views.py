#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""views"""

import flask

views: flask.Blueprint = flask.Blueprint("views", __name__)


@views.get("/")
@views.get("/index.html")
def index() -> str:
    """index page"""
    return flask.render_template("index.j2")
