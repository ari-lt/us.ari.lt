#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""utils"""

from typing import Optional

import flask
from flask_ishuman import CaptchaGenerator

from .c import c


def jscaptcha() -> Optional[CaptchaGenerator]:
    """return js-friendly captcha"""
    return c.new() if "nojs" in flask.request.args else None


def flash_render(
    msg: str, template: str, captcha: bool = True, level: str = "error"
) -> str:
    """flash and render"""

    flask.flash(msg, level)
    return flask.render_template(template, **({"c": jscaptcha()} if captcha else {}))
