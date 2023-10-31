#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""authentication"""

import flask
import typing as t

from .c import c
from .routing import Bp

auth: Bp = Bp("auth", __name__)


@auth.post("/signup")
def signup() -> t.Tuple[str, int]:
    username: t.Optional[str] = flask.request.form.get("username")
    password: t.Optional[str] = flask.request.form.get("password")
    code: t.Optional[str] = flask.request.form.get("code")

    if not all((username, password, code)):
        return "invalid request", 400

    if not c.verify(code):
        return "invalid captcha", 403

    return "handle sign up", 200
