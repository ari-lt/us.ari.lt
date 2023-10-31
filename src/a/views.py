#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""views"""

import flask

from .c import c
from .routing import Bp

views: Bp = Bp("views", __name__)


@views.get("/")
def index() -> str:
    return flask.render_template("index.j2", c=c.new())
