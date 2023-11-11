#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""utils"""

from typing import Optional, Any

import flask

from . import const
from .c import OggCaptchaGenerator, c


def jscaptcha() -> Optional[OggCaptchaGenerator]:
    """return js-friendly captcha"""

    return (
        OggCaptchaGenerator.from_gen(c.new()) if "nojs" in flask.request.args else None
    )


def flash_render(
    msg: str,
    template: str,
    captcha: bool = True,
    level: str = "error",
    **kwargs: Any,
) -> str:
    """flash and render"""

    flask.flash(msg, level)
    return flask.render_template(
        template,
        **({"c": jscaptcha()} if captcha else {}),
        pw_len=const.MAX_PW_LEN,
        pin_len=const.PIN_LEN,
        username_len=const.USERNAME_LEN,
        **kwargs,
    )


def validate_username(username: str) -> bool:
    """returns if a username is valid or not"""

    for char in username:
        if not (char.isalnum() or char in "._+-"):
            return False

    return True
