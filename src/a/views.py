#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""views"""

from __future__ import annotations

import flask
import flask_ishuman

from .routing import Bp

views: Bp = Bp("views", __name__)
c: flask_ishuman.IsHuman = flask_ishuman.IsHuman()


@views.get("/")
def index() -> str:
    return flask.render_template("index.j2", c=c.new())
