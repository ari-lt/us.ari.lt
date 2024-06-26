#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""a.ari.lt"""

import base64
import os
import re
import secrets
import time
from datetime import timedelta
from functools import lru_cache
from typing import Any, Dict, Optional, Tuple

import flask
import web_mini
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager  # type: ignore
from werkzeug.exceptions import HTTPException
from werkzeug.routing import Rule
from werkzeug.wrappers import Response

from . import const, crypt, models, util
from .util import is_admin, require_role
from .md import get_code_style


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

    # manifest

    if os.path.isfile("manifest.json"):
        with open("manifest.json", "r") as fp:
            m: str = fp.read()

        @app.route("/manifest.json")
        def __manifest__() -> flask.Response:
            """new route"""
            return flask.Response(m, mimetype="application/json")

    # favicon

    @app.route("/favicon.ico", methods=["GET", "POST"])
    def __favicon__() -> Response:
        """favicon"""
        return flask.redirect("https://ari.lt/favicon.ico")

    # robots

    @app.route("/robots.txt", methods=["GET", "POST"])
    def __robots__() -> Response:
        """favicon"""

        robots: str = f"User-agent: *\nAllow: *\n\
Sitemap: {app.config['PREFERRED_URL_SCHEME']}://{app.config['DOMAIN']}/sitemap.xml\n"

        for blog in models.Blog.query.all():  # type: ignore
            robots += f"Sitemap: {app.config['PREFERRED_URL_SCHEME']}://{app.config['DOMAIN']}/blog/@{blog.username}/sitemap.xml\n"  # type: ignore

        return flask.Response(robots, mimetype="text/plain")

    # gen sitemap

    rule: Rule

    pat: re.Pattern[str] = re.compile(r"<.+?:(.+?)>")

    sitemap: str = '<?xml version="1.0" encoding="UTF-8"?>\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'

    def surl(loc: str) -> str:
        """sitemap url"""

        u: str = "<url>"
        u += f'<loc>{app.config["PREFERRED_URL_SCHEME"]}://{app.config["DOMAIN"]}{loc}</loc>'
        u += "<priority>1.0</priority>"
        return u + "</url>"

    sitemap += surl("/robots.txt")
    sitemap += surl("/manifest.json")
    sitemap += surl("/LICENSE")

    for rule in app.url_map.iter_rules():
        url: str = pat.sub(r"\1", rule.rule)
        sitemap += surl(url)

    sitemap = sitemap.replace("@user", f"@{app.config['OWNER_USER']}")

    @app.route("/sitemap.xml", methods=["GET", "POST"])
    def __sitemap__() -> flask.Response:
        """sitemap"""
        esitemap: str = sitemap

        for user in models.User.query.all():  # type: ignore
            esitemap += surl(f"/@{user.username}")  # type: ignore

        for blog in models.Blog.query.all():  # type: ignore
            esitemap += surl(f"/blog/@{blog.username}")  # type: ignore

            if blog.username == app.config["OWNER_USER"]:  # type: ignore
                for post in blog.posts:  # type: ignore
                    esitemap += surl(f"/blog/@{blog.username}/{post.slug}")  # type: ignore

        return flask.Response(esitemap + "</urlset>", mimetype="application/xml")

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

    # admin

    if not os.path.exists("admin.key"):
        with open("admin.key", "wb") as fp:
            fp.write(secrets.SystemRandom().randbytes(2**14))

    with open("admin.key", "rb") as fp:
        app.config["ADMIN_KEY"] = fp.read()

    app.config["PREFERRED_URL_SCHEME"] = "http" if app.debug else "https"
    app.config["DOMAIN"] = "us.ari.lt"

    app.config["OWNER_USER"] = "ari"

    app.config["CAPTCHA_PEPPER_FILE"] = "captcha.key"
    app.config["CAPTCHA_EXPIRY"] = 60 * 10  # 10 minutes
    app.config["CAPTCHA_CHARSET"] = "abdefghmnqrtyzABDEFGHLMNRTYZ2345689#@%?!"
    app.config["CAPTCHA_RANGE"] = (4, 6)

    app.config["SESSION_COOKIE_SAMESITE"] = "strict"
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=4)

    app.config["REMEMBER_COOKIE_NAME"] = "authorization"
    app.config["REMEMBER_COOKIE_SAMESITE"] = "strict"
    app.config["REMEMBER_COOKIE_SECURE"] = True

    app.config["USE_SESSION_FOR_NEXT"] = True

    app.config[
        "SQLALCHEMY_DATABASE_URI"
    ] = f"mysql+pymysql://{maria_user}:{maria_pass}@127.0.0.1/main?charset=utf8mb4"
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["ARGON2_TIME_COST"] = 4
    app.config["ARGON2_PARALLELISM"] = os.cpu_count() or 4
    app.config["ARGON2_SALT_LENGTH"] = const.ARGON2_SALT_LENGTH
    app.config["ARGON2_HASH_LENGTH"] = const.ARGON2_HASH_LENGTH

    app.config["CACHE_TYPE"] = "MemcachedCache"

    from . import cache

    cache.blog.init_app(app)  # type: ignore

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
        """limit all requests and upgrade urls"""

        if app.debug or app.config["PREFERRED_URL_SCHEME"] != "https":
            return

        try:
            if flask.request.url[:7] == "http://":
                flask.request.url = f"https://{flask.request.url[7:]}"
        except Exception:
            pass

    @app.after_request
    def _(response: flask.Response) -> flask.Response:
        """minify resources"""

        # wher .update() ??11/!?@?/

        if not app.debug:
            response.headers["Content-Security-Policy"] = "upgrade-insecure-requests"
            response.headers[
                "Strict-Transport-Security"
            ] = "max-age=63072000; includeSubDomains; preload"

        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

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

    def b64(data: str) -> str:
        """base64"""
        return base64.b64encode(data.encode()).decode("ascii")

    @app.context_processor  # type: ignore
    def _() -> Dict[str, Any]:
        """expose functions"""
        return {
            "require_role": require_role,
            "Role": const.Role,
            "CodeTheme": const.CodeTheme,
            "pin_len": const.PIN_LEN,
            "name_len": const.NAME_LEN,
            "username_len": const.USERNAME_LEN,
            "bio_len": const.USERNAME_LEN,
            "origin_len": const.COUNTER_ORIGIN_LEN,
            "rurl": flask.request.host_url + flask.request.path[1:],
            "is_admin": is_admin,
            "blog_post_slug_len": const.BLOG_POST_SLUG_LEN,
            "blog_post_keywords_len": const.BLOG_POST_KEYWORDS_LEN,
            "blog_post_content_len": const.BLOG_POST_CONTENT_LEN,
            "blog_post_description_len": const.BLOG_POST_DESCRIPTION_LEN,
            "blog_primary_len": const.BLOG_PRIMARY_LEN,
            "blog_secondary_len": const.BLOG_SECONDARY_LEN,
            "blog_locale_len": const.BLOG_LOCALE_LEN,
            "blog_comment_url_len": const.BLOG_COMMENT_URL_LEN,
            "blog_visitor_url_len": const.BLOG_VISITOR_URL_LEN,
            "trunc": util.trunc,
            "b64": b64,
            "blog_post_section_delim": const.BLOG_POST_SECTION_DELIM,
            "min_css": min_css,
            "e2j": const.enum2json,
            "get_code_style": get_code_style,
        }

    from .c import c

    c.init_app(app)

    from .views import views

    app.register_blueprint(views, url_prefix="/")

    assign_http(assign_apps(app))

    return app
