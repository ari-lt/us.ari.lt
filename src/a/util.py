#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""utils"""

from functools import wraps
from typing import Any, Callable, NoReturn, Optional, Tuple

import flask
from flask_login import current_user, login_required  # type: ignore
from subprocess import check_output

from . import const, crypt, models
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
        **kwargs,
    )


def flash_abort(msg: str, code: int, level: str = "message") -> NoReturn:
    """flash and abort"""
    flask.flash(msg, level)
    flask.abort(code)


def validate_username(username: str) -> bool:
    """returns if a username is valid or not"""

    for char in username:
        if not (char.isalnum() or char in "._+-"):
            return False

    return True


def require_role(role: const.Role, allow_limit: bool = True) -> bool:
    """require a role"""

    if current_user.is_anonymous:  # type: ignore
        return False

    if (not allow_limit) and current_user.limited:  # type: ignore
        return False

    return role.value <= current_user.role.value  # type: ignore


def require_role_route(
    *r_args: Any,
    **r_kwargs: Any,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """require a role ( flask )"""

    def decorate(fn: Callable[..., Any]) -> Callable[..., Any]:
        """decorate require_role_route"""

        @wraps(fn)
        @login_required
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """function wrapper"""

            if require_role(*r_args, **r_kwargs):
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

        if not flask.current_app.debug and not c.verify(flask.request.form.get("code")):
            flask.flash("invalid CAPTCHA", "error")
            return flask.redirect(flask.request.url)

        return fn(*args, **kwargs)

    return wrapper


def make_api(response: flask.Response, cors: bool = True) -> flask.Response:
    """make api endpoint ( disables cors and caching )"""

    response.headers["Expires"] = "Thu, 01 Jan 1970 00:00:00 GMT"
    response.headers[
        "Cache-Control"
    ] = "max-age=0, no-cache, must-revalidate, proxy-revalidate"

    if cors:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"

    return response


def api(fn: Callable[..., Any]) -> Callable[..., Any]:
    """api endpoint"""

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> flask.Response:
        """decorator"""
        return make_api(flask.make_response(fn(*args, **kwargs)))

    return wrapper


def clear_admin() -> None:
    """clear admin"""

    flask.session.permanent = False
    flask.session.pop("__admin__", None)


def is_admin() -> bool:
    """checks if user is admin"""

    if "__admin__" not in flask.session:
        return False

    try:
        if len(flask.session["__admin__"]) != 3:
            clear_admin()
            return False
    except Exception:
        return False

    admin: bool = models.argon2.check_password_hash(  # type: ignore
        flask.session["__admin__"][0],
        flask.current_app.config["ADMIN_KEY"] + flask.current_app.config["SECRET_KEY"],
    )

    if admin:
        return admin
    else:
        clear_admin()
        return False


def set_admin() -> None:
    """set admin session"""

    flask.session.permanent = True

    flask.session["__admin__"] = (
        models.argon2.generate_password_hash(flask.current_app.config["ADMIN_KEY"] + flask.current_app.config["SECRET_KEY"]),  # type: ignore
        crypt.encrypt_aes(
            current_user.username,  # type: ignore
            flask.current_app.config["SECRET_KEY"],
            flask.current_app.config["ADMIN_KEY"],
        ),
        flask.current_app.config["REMEMBER_COOKIE_NAME"] in flask.request.cookies,
    )


def get_admin() -> Optional[Tuple[str, bool]]:
    """get admin username if available"""

    if is_admin():
        try:
            remember: bool = flask.session["__admin__"][2]
        except Exception:
            remember = False

        user: str = crypt.decrypt_aes(
            flask.session["__admin__"][1],
            flask.current_app.config["SECRET_KEY"],
            flask.current_app.config["ADMIN_KEY"],
        )

        return user, remember

    return None


def get_admin_user() -> Optional[Any]:
    """get admin user"""

    admin: Optional[Tuple[str, bool]] = get_admin()

    if admin:
        return models.User.query.filter_by(username=admin[0]).first_or_404()

    return None


def get_origin() -> Optional[str]:
    """get origin"""
    return flask.request.headers.get("Origin", flask.request.referrer)


def trunc(data: str, length: int, end: str = " ...") -> str:
    """truncate data"""
    return data[:length] + (end if len(data) > length else "")


def get_network() -> Tuple[int, int, int]:
    """get network usage in bytes

    rx, tx, oc"""

    oc: int = max(len(check_output(["ss", "-Hntu"]).splitlines()) - 1, 0)

    for line in open("/proc/net/dev", "r"):
        if "lo" not in line and ":" in line:
            data = line.split()
            return int(data[1]), int(data[9]), oc

    return 0, 0
