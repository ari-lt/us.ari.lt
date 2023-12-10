#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""views"""

import os
import subprocess
import typing as t

import flask
from werkzeug.wrappers import Response

from . import models, util
from .routing import Bp

views: Bp = Bp("views", __name__)


@views.get("/")
def index() -> str:
    """index"""

    with open("/proc/loadavg", "r") as fp:
        loadavg: str = fp.read().strip()

    rx, tx, oc = util.get_network()
    cpu: int = os.cpu_count() or 1

    return flask.render_template(
        "index.j2",
        users=models.User.query.all(),
        free=subprocess.check_output(("free", "-h")).decode().strip(),
        lsblk=subprocess.check_output(
            ("lsblk", "-ifo", "NAME,FSTYPE,FSVER,FSAVAIL,FSUSE%")
        )
        .decode()
        .strip(),
        loadavg=loadavg,
        cpu=f"{float(loadavg.split(maxsplit=1)[0]) / cpu * 100:.3f}% | {cpu} threads",
        net=f"rx {rx / 1024 / 1024:.3f} mb, tx {tx / 1024 / 1024:.3f} mb, open {oc}",
        date=subprocess.check_output(("date",)).decode().strip(),
    )


@views.get("/tos")
def tos() -> str:
    """terms of service"""
    return flask.render_template("tos.j2")


@views.get("/@<string:username>")
@views.get("/@<string:username>/")
def user(username: str) -> t.Union[str, t.Tuple[str, int]]:
    """index"""

    user: t.Optional[models.User] = models.db.session.get(models.User, username)

    if user is None:
        return flask.render_template("404.j2"), 404

    return flask.render_template(
        "user.j2",
        user=user,
        apps=models.App.query.filter_by(username=username).all(),
    )


@views.get("/git", defaults={"_": ""})
@views.get("/git/", defaults={"_": ""})
@views.get("/git/<path:_>")
def git(_: str) -> Response:
    """git source"""
    return flask.redirect(
        f"https://ari.lt/lh/us.ari.lt/{flask.request.full_path[4:]}", code=302
    )


@views.get("/blank")
@views.get("/blank/")
def blank() -> str:
    """blank page"""
    return flask.render_template("base.j2")


@views.get("/LICENSE")
@views.get("/license")
def license() -> Response:
    """license"""
    return flask.redirect("https://www.gnu.org/licenses/gpl-3.0.en.html")
