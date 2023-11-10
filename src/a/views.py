#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""views"""

from typing import Union

import flask
from flask_login import login_required  # type: ignore
from werkzeug.wrappers import Response

from .routing import Bp

views: Bp = Bp("views", __name__)


@views.get("/")
@login_required
def index() -> Union[str, Response]:
    """index"""
    return flask.render_template("index.j2")
