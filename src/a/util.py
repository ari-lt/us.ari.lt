#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""utils"""

from functools import wraps
from typing import Any, Callable, Optional

import flask
from flask_login import current_user, login_required  # type: ignore

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


def require_role(role: const.Role) -> bool:
    """require a role"""
    return not current_user.is_anonymous and role.value <= current_user.role.value  # type: ignore


def require_role_route(
    role: const.Role,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """require a role ( flask )"""

    def decorate(fn: Callable[..., Any]) -> Callable[..., Any]:
        """decorate require_role_route"""

        @wraps(fn)
        @login_required
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """function wrapper"""

            if require_role(role):
                return fn(*args, **kwargs)
            else:
                flask.abort(403)

        return wrapper

    return decorate


def captcha(fn: Callable[..., Any]) -> Callable[..., Any]:
    """dont allow users through without captcha"""

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """decorator"""

        # TODO better handling of invalid captcha, rn it just returns 302 which returns 200
        # which sucks and does not properly indicate error

        if not c.verify(flask.request.form.get("code")):
            flask.flash("invalid CAPTCHA", "error")
            return flask.redirect(flask.request.url)

        return fn(*args, **kwargs)

    return wrapper
