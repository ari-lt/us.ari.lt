#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""visitors counter"""

import typing as t

import flask
from flask_login import current_user, login_required  # type: ignore
from werkzeug.wrappers import Response

from .. import const, models, util
from ..routing import Bp

counter: Bp = Bp("counter", __name__)


@counter.get("/")
@login_required  # type: ignore
def index() -> str:
    """render counter index page"""
    return flask.render_template(
        "counter.j2",
        counters=models.Counter.query.filter_by(username=current_user.username).all(),  # type: ignore
        c=util.jscaptcha(),
    )


@counter.post("/")
@util.captcha
@login_required  # type: ignore
def create_counter() -> flask.Response:
    name: t.Optional[str] = flask.request.form.get("name")
    init: t.Optional[str] = flask.request.form.get("init")
    origins: t.Optional[str] = flask.request.form.get("origins")

    if not name or init is None:
        flask.abort(400)

    try:
        init_int: int = int(init) % const.HUGEINT_MAX
    except ValueError:
        flask.abort(400)

    try:
        counter: models.Counter = models.Counter(name, current_user.username, init_int, origins)  # type: ignore
        current_user.counters.append(counter)  # type: ignore
        models.db.session.commit()
    except Exception:
        flask.flash("unable to create a counter")
        flask.abort(500)

    return flask.redirect("@" + current_user.username + "/" + counter.id)  # type: ignore


@counter.get("/@<string:user>/<string:id>")
@login_required  # type: ignore
def manage_counter_page(user: str, id: str) -> str:
    """manage counter page"""

    if user != current_user.username:  # type: ignore
        flask.abort(401)

    return flask.render_template(
        "counter_manage.j2",
        counter=models.Counter.query.filter_by(username=user, id=id).first_or_404(),  # type: ignore
        c=util.jscaptcha(),
    )


@counter.post("/@<string:user>/<string:id>")
@util.captcha
@login_required  # type: ignore
def manage_counter(user: str, id: str) -> Response:
    """manage counter"""

    if user != current_user.username:  # type: ignore
        flask.abort(401)

    counter: models.Counter = models.Counter.query.filter_by(
        username=user, id=id
    ).first_or_404()

    name: t.Optional[str] = flask.request.form.get("name")
    count: t.Optional[str] = flask.request.form.get("count")
    origins: t.Optional[str] = flask.request.form.get("origins")

    if name is not None:
        try:
            counter.set_name(name)
        except Exception:
            flask.abort(403)

    if count is not None:
        try:
            counter.set_count(int(count))
        except Exception:
            flask.abort(403)

    if origins is not None:
        try:
            counter.set_origins(origins)
        except Exception:
            flask.abort(403)

    try:
        models.db.session.commit()
    except Exception:
        flask.flash("failed to edit the counter")
        flask.abort(501)

    flask.flash("the counter was edited")
    return flask.redirect(flask.url_for("counter.index"))


@counter.get("/@<string:user>/<string:id>.txt")
def counter_text(user: str, id: str) -> flask.Response:
    """render counter as text"""

    counter: models.Counter = models.Counter.query.filter_by(username=user, id=id).first_or_404()  # type: ignore

    response: flask.Response = util.make_api(flask.Response(str(counter.inc_or_404().count), mimetype="text/plain"))  # type: ignore
    response.headers["Access-Control-Allow-Origin"] = counter.origins
    response.headers["Access-Control-Allow-Methods"] = "GET"

    return response


@counter.get("/@<string:user>/<string:id>.svg")
def counter_svg(user: str, id: str) -> flask.Response:
    """render counter as svg"""

    fill: t.Optional[str] = flask.request.args.get("fill")
    font: t.Optional[str] = flask.request.args.get("font")

    floats: t.Dict[str, float] = {}

    for arg in "size", "baseline", "ratio", "padding":
        try:
            floats[arg] = float(flask.request.args.get(arg))  # type: ignore
        except Exception:
            pass

    counter: models.Counter = models.Counter.query.filter_by(username=user, id=id).first_or_404()  # type: ignore

    response: flask.Response = util.make_api(
        flask.Response(
            counter.inc_or_404().to_svg(  # type: ignore
                fill=fill,
                font=font,
                **floats,
            ),
            mimetype="image/svg+xml",
        )
    )

    response.headers["Access-Control-Allow-Origin"] = counter.origins
    response.headers["Access-Control-Allow-Methods"] = "GET"

    return response
