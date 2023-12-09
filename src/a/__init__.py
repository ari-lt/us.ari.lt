#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""a.ari.lt"""

import base64
import os
import re
import secrets
import time
from functools import lru_cache, partial
from typing import Any, Dict, Optional, Tuple

import flask
import web_mini
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager  # type: ignore
from werkzeug.exceptions import HTTPException
from werkzeug.routing import Rule

from . import const, crypt
from .util import require_role


def random_cookie_salt() -> str:
    """generates a random cookie salt"""
    return base64.b85encode(crypt.RAND.randbytes(64)).decode("ascii")


@lru_cache
def min_css(css: str) -> str:
    """minify css"""
    return web_mini.css.minify_css(css)


def assign_apps(
    app: flask.Flask,
    app_dir: str = os.path.dirname(__file__) + "/app",
) -> flask.Flask:
    """assign all apps in `app_dir` directory"""

    app.config["SUBAPPS"] = []

    d: str = os.getcwd()

    b: str = os.path.basename(app_dir)

    os.chdir(app_dir)

    for subapp in os.listdir(app_dir):
        if ".py" != subapp[-3:] or not os.path.isfile(subapp):
            continue

        mod: str = os.path.splitext(subapp)[0]

        if mod[0] == "_":
            continue

        app.logger.debug(f"setting {mod!r} up")

        exec(f"from .{b}.{mod} import {mod}")
        app.register_blueprint(eval(mod), url_prefix=f"/{mod}")
        app.config["SUBAPPS"].append(subapp[:-3])

    os.chdir(d)

    return app


def assign_http(app: flask.Flask) -> flask.Flask:
    """assign http file stuff"""

    def _new_route(content: str, mime: str) -> flask.Response:
        """new route"""

        return flask.Response(content, mimetype=mime)

    for file, mime in (
        ("robots.txt", "text/plain"),
        ("manifest.json", "application/json"),
        ("favicon.ico", "image/vnd.microsoft.icon"),
    ):
        if not os.path.isfile(file):
            continue

        with open(file, "r") as fp:
            part: partial[flask.Response] = partial(_new_route, fp.read(), mime)
            part.__name__ = "_" + file.replace(".", "_")  # type: ignore
            app.route(f"/{file}", methods=["GET", "POST"])(part)  # type: ignore

    # gen sitemap

    rule: Rule

    pat: re.Pattern[str] = re.compile(r"<.+?:(.+?)>")

    sitemap: str = '<?xml version="1.0" encoding="UTF-8"?>\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'

    for rule in app.url_map.iter_rules():
        url: str = pat.sub(r"\1", rule.rule)

        sitemap += "<url>"
        sitemap += f'<loc>{app.config["PREFERRED_URL_SCHEME"]}://{app.config["DOMAIN"]}{url}</loc>'
        sitemap += "<priority>1.0</priority>"
        sitemap += "</url>"

    sitemap += "</urlset>"
    sitemap = sitemap.replace("@user", f"@{app.config['OWNER_USER']}")

    @app.route("/sitemap.xml", methods=["GET", "POST"])
    def _() -> flask.Response:
        """sitemap"""
        return flask.Response(sitemap, mimetype="application/xml")

    return app


def create_app(maria_user: str, maria_pass: str) -> flask.Flask:
    """create a new flask app"""

    web_mini.compileall()

    app: flask.Flask = flask.Flask(__name__)

    # secret

    if not os.path.exists("secret.key"):
        with open("secret.key", "wb") as fp:
            fp.write(secrets.SystemRandom().randbytes(2**14))

    with open("secret.key", "rb") as fp:
        app.config["SECRET_KEY"] = fp.read()

    app.config["PREFERRED_URL_SCHEME"] = "https"
    app.config["DOMAIN"] = "us.ari.lt"

    app.config["OWNER_USER"] = "ari"

    app.config["CAPTCHA_PEPPER_FILE"] = "captcha.key"
    app.config["CAPTCHA_EXPIRY"] = 60 * 10  # 10 minutes
    app.config["CAPTCHA_CHARSET"] = "abdefghmnqrtyzABDEFGHLMNRTYZ2345689#@%?!"
    app.config["CAPTCHA_RANGE"] = (4, 6)

    app.config["SESSION_COOKIE_SAMESITE"] = "strict"
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True

    app.config["REMEMBER_COOKIE_NAME"] = "authorization"
    app.config["REMEMBER_COOKIE_SAMESITE"] = "strict"
    app.config["REMEMBER_COOKIE_SECURE"] = True

    app.config["USE_SESSION_FOR_NEXT"] = True

    app.config[
        "SQLALCHEMY_DATABASE_URI"
    ] = f"mysql+pymysql://{maria_user}:{maria_pass}@127.0.0.1/main"
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["ARGON2_TIME_COST"] = 4
    app.config["ARGON2_PARALLELISM"] = os.cpu_count() or 4
    app.config["ARGON2_SALT_LENGTH"] = const.ARGON2_SALT_LENGTH
    app.config["ARGON2_HASH_LENGTH"] = const.ARGON2_HASH_LENGTH

    from .models import User, argon2, db

    db.init_app(app)

    with app.app_context():
        db.create_all()

    argon2.init_app(app)  # type: ignore

    lm: LoginManager = LoginManager(app)
    limit: Limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["10000 per day", "1500 per hour", "50 per minute"],
        storage_uri="memory://",
    )

    lm.login_view = "auth.signin"  # type: ignore
    lm.refresh_view = "auth.signin"  # type: ignore
    lm.session_protection = "strong"  # type: ignore
    lm.login_message = "please sign in"  # type: ignore
    lm.needs_refresh_message = "your login expired, please sign in again"  # type: ignore

    @lm.user_loader  # type: ignore
    def _(username: str) -> Optional[User]:
        """load user by username"""

        if username and len(username) <= const.USERNAME_LEN:
            return User.get_by_user(username)

    @app.before_request
    @limit.limit("")
    def _() -> None:
        """limit all requests"""

    @app.after_request
    def _(response: flask.Response) -> flask.Response:
        """minify resources"""

        # wher .update() ??11/!?@?/

        response.headers[
            "Strict-Transport-Security"
        ] = "max-age=63072000; includeSubDomains; preload"
        response.headers["X-Frame-Options"] = "deny"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = "upgrade-insecure-requests"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Referrer-Policy"] = "no-referrer"

        if response.direct_passthrough:
            return response

        response_data: str = response.get_data(as_text=True)

        if response.content_type == "text/html; charset=utf-8":
            minified_data: str = web_mini.html.minify_html(response_data)
        elif response.content_type == "text/css; charset=utf-8":
            minified_data: str = min_css(response_data)
        else:
            return response

        return app.response_class(
            response=minified_data,
            status=response.status,
            headers=dict(response.headers),
            mimetype=response.mimetype,
        )

    @app.errorhandler(HTTPException)
    def _(e: HTTPException) -> Tuple[Any, int]:
        """handle http errors"""

        if e.code == 429:
            time.sleep(crypt.RAND.random() * 15)

            return (
                flask.Response(
                    f"too many requests : {e.description or '<limit>'}",
                    mimetype="text/plain",
                ),
                429,
            )

        return (
            flask.render_template(
                "http.j2",
                code=e.code,
                summary=e.name.lower(),
                description=(e.description or f"http error code {e.code}").lower(),
            ),
            e.code or 200,
        )

    @app.context_processor  # type: ignore
    def _() -> Dict[str, Any]:
        """expose functions"""
        return {
            "require_role": require_role,
            "Role": const.Role,
            "pin_len": const.PIN_LEN,
            "name_len": const.NAME_LEN,
            "username_len": const.USERNAME_LEN,
            "bio_len": const.USERNAME_LEN,
            "origins_len": const.COUNTER_ORIGINS_LEN,
            "rurl": flask.request.host_url + flask.request.path[1:],
        }

    from .c import c

    c.init_app(app)

    from .views import views

    app.register_blueprint(views, url_prefix="/")

    assign_http(assign_apps(app))

    return app
