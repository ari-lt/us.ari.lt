#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""blogging"""

import typing as t
import xml.etree.ElementTree as etree
from datetime import datetime
from time import sleep

import flask
from flask_login import current_user  # type: ignore
from werkzeug.wrappers import Response

from .. import cache, const, models, util
from ..routing import Bp

blog: Bp = Bp("blog", __name__)


@blog.get("/")
@util.require_role_route(const.Role.user)
def index() -> str:
    """blogging"""
    return flask.render_template(
        "blog_conf.j2",
        c=util.jscaptcha(),
        mblog=current_user.blog,  # type: ignore
    )


@blog.post("/")
@util.captcha
@util.require_role_route(const.Role.user)
def blog_conf() -> Response:
    """blogging"""

    conf: t.Dict[str, t.Optional[str]] = {
        "title": flask.request.form.get("title"),
        "header": flask.request.form.get("header"),
        "description": flask.request.form.get("description"),
        "keywords": flask.request.form.get("keywords"),
        "default_keywords": flask.request.form.get("default_keywords"),
        "primary": flask.request.form.get("primary"),
        "secondary": flask.request.form.get("secondary"),
        "locale": flask.request.form.get("locale"),
        "visitor_url": flask.request.form.get("visitor"),
        "comment_url": flask.request.form.get("comment"),
        "code_theme": flask.request.form.get("code_theme"),
    }

    if current_user.blog is None:  # type: ignore
        try:
            current_user.blog = models.Blog(username=current_user.username, **conf)  # type: ignore
        except Exception as e:
            flask.current_app.log_exception(e)
            flask.flash("failed to create blog, bad request", "error")
            flask.abort(400)
    else:
        for key, value in conf.items():
            if value is None:
                continue

            try:
                fn: t.Optional[t.Callable[[str], None]] = getattr(current_user.blog, f"set_{key}", None)  # type: ignore

                if fn is not None:
                    fn(value)
            except Exception as e:
                flask.current_app.log_exception(e)
                flask.flash(f"failed to set {key!r}", "error")

    try:
        models.db.session.commit()
        flask.flash("blog updated", "info")
    except Exception as e:
        models.db.session.rollback()
        flask.current_app.log_exception(e)
        flask.flash("failed updating the blog", "error")
        flask.abort(500)

    return flask.redirect(flask.url_for("blog.index"))


@blog.get("/@<string:user>")
def user_blog(user: str) -> str:
    """show user's blog"""

    usr: models.User = models.User.query.filter_by(username=user).first_or_404()
    blog: t.Optional[models.Blog] = usr.blog

    if blog is None:
        flask.abort(404)

    return flask.render_template(
        "blog.j2",
        c=util.jscaptcha(),
        blog=blog,
        posts=models.BlogPost.query.filter_by(username=user)
        .order_by(models.BlogPost.posted.desc())  # type: ignore
        .all(),
        style=((usr.blog.style or "") if usr.blog else "").split(
            const.BLOG_POST_SECTION_DELIM, 1
        )[0],
    )


@blog.get("/@<string:user>/")
def user_blog_dir(user: str) -> Response:
    """redirect back to file"""
    return flask.redirect(flask.url_for("blog.user_blog", user=user))


@blog.route("/@<string:user>/robots.txt")
def robots(user: str) -> Response:
    """robots.txt"""

    del user

    return flask.Response(
        f"""
User-agent: *
Allow: *
Sitemap: {flask.request.url[:-11]}/sitemap.xml
Sitemap: {flask.current_app.config['PREFERRED_URL_SCHEME']}://{flask.current_app.config['DOMAIN']}/sitemap.xml
""".strip(),
        mimetype="text/plain",
    )


@blog.route("/@<string:user>/theme.txt")
def theme(user: str) -> Response:
    """theme file"""

    return flask.Response(
        (models.Blog.query.filter_by(username=user).first_or_404().style or "")
        + f"""

/* see {flask.request.url[:-10]}/post.css and {flask.request.url[:-10]}/blog.css for individual files
 * licensed under GPLv3+ https://www.gnu.org/licenses/gpl-3.0.en.html */
""".strip(),
        mimetype="text/plain",
    )


@blog.route("/@<string:user>/blog.css")
def blog_css(user: str) -> Response:
    """blog css"""

    return flask.Response(
        (models.Blog.query.filter_by(username=user).first_or_404().style or "").split(
            const.BLOG_POST_SECTION_DELIM, 1
        )[0],
        mimetype="text/css",
    )


@blog.route("/@<string:user>/post.css")
def post_css(user: str) -> Response:
    """post css"""

    return flask.Response(
        (models.Blog.query.filter_by(username=user).first_or_404().style or "").replace(
            const.BLOG_POST_SECTION_DELIM, "", 1
        ),
        mimetype="text/css",
    )


@blog.route("/@<string:user>/sitemap.xml")
def sitemap(user: str) -> Response:
    """manifest"""

    ftime: str = "%Y-%m-%dT%H:%M:%S+00:00"

    posts: t.List[models.BlogPost] = (
        models.BlogPost.query.filter_by(username=user)
        .order_by(models.BlogPost.posted.desc())  # type: ignore
        .all()
    )

    if not posts:
        flask.abort(404)

    root: etree.Element = etree.Element("urlset")
    root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    for file in ("robots.txt", "manifest.json", "rss.xml"):
        url: etree.Element = etree.SubElement(root, "url")

        etree.SubElement(url, "loc").text = f"{flask.request.url[:-12]}/{file}"
        etree.SubElement(url, "lastmod").text = posts[0].edited.strftime(ftime)  # type: ignore
        etree.SubElement(url, "priority").text = "1.0"

    for post in posts:
        url = etree.SubElement(root, "url")

        etree.SubElement(url, "loc").text = f"{flask.request.url[:-12]}/{post.slug}"
        etree.SubElement(url, "lastmod").text = post.edited.strftime(ftime)  # type: ignore
        etree.SubElement(url, "priority").text = "1.0"

    return flask.Response(
        etree.tostring(
            root,
            encoding="UTF-8",
            xml_declaration=True,
        ),
        mimetype="application/xml",
    )


@blog.route("/@<string:user>/manifest.json")
def manifest(user: str) -> Response:
    """manifest"""

    blog: models.Blog = models.Blog.query.filter_by(username=user).first_or_404()

    return flask.jsonify(  # type: ignore
        {
            "$schema": "https://json.schemastore.org/web-manifest-combined.json",
            "short_name": blog.header,
            "name": blog.title,
            "description": blog.description,
            "start_url": ".",
            "display": "standalone",
            "theme_color": blog.primary,
            "background_color": blog.secondary,
            "icons": [
                {"src": "/favicon.ico", "sizes": "128x128", "type": "image/x-icon"}
            ],
        }
    )


@blog.route("/@<string:user>/rss.xml")
def rss(user: str) -> Response:
    """rss feed"""

    ftime: str = "%a, %d %b %Y %H:%M:%S GMT"

    blog: models.Blog = models.Blog.query.filter_by(username=user).first_or_404()
    posts: t.List[models.BlogPost] = (
        models.BlogPost.query.filter_by(username=user)
        .order_by(models.BlogPost.posted.desc())  # type: ignore
        .all()
    )

    root: etree.Element = etree.Element("rss")
    root.set("version", "2.0")

    channel: etree.Element = etree.SubElement(root, "channel")

    etree.SubElement(channel, "title").text = blog.title
    etree.SubElement(channel, "link").text = flask.request.url[:-8]
    etree.SubElement(channel, "description").text = blog.description
    etree.SubElement(channel, "generator").text = "ari-web user accounts and services"
    etree.SubElement(channel, "language").text = blog.locale.lower().replace("_", "-")

    if posts:
        etree.SubElement(channel, "lastBuildDate").text = posts[0].edited.strftime(ftime)  # type: ignore

    for post in posts:
        item: etree.Element = etree.SubElement(channel, "item")
        link: str = f"{flask.request.url[:-8]}/{post.slug}"

        etree.SubElement(item, "title").text = post.title
        etree.SubElement(item, "link").text = link
        etree.SubElement(item, "description").text = (
            post.description + f" [last edited at {post.edited}]"
        )
        etree.SubElement(item, "pubDate").text = post.posted.strftime(ftime)  # type: ignore
        etree.SubElement(item, "guid").text = link

    return flask.Response(
        etree.tostring(
            root,
            encoding="UTF-8",
            xml_declaration=True,
        ),
        mimetype="application/xml+rss",
    )


@blog.get("/~preview")
@blog.get("/~preview/")
@util.require_role_route(const.Role.user)
def preview() -> str:
    """preview user's preview"""

    if (
        "ctx" in flask.request.args
        and (
            render := cache.blog_get(
                current_user.username,  # type: ignore
                flask.request.args["ctx"],  # type: ignore
            )
        )
        is not None
    ):
        return render

    flask.abort(404)


@blog.get("/@<string:user>/<string:slug>")
def show_post(user: str, slug: str) -> str:
    """show user's blog post"""

    usr: models.User = models.User.query.filter_by(username=user).first_or_404()
    blog: t.Optional[models.Blog] = usr.blog

    return flask.render_template(
        "blog_post.j2",
        blog=blog,
        post=models.BlogPost.query.filter_by(username=user, slug=slug).first_or_404(),
        style=((blog.style or "") if blog else "").replace(
            const.BLOG_POST_SECTION_DELIM, "", 1
        ),
    )


@blog.get("/@<string:user>/<string:slug>/")
def show_blog_dir(user: str, slug: str) -> Response:
    """redirect back to file"""
    return flask.redirect(flask.url_for("blog.show_post", user=user, slug=slug))


@blog.get("/@<string:user>/~new")
@util.require_role_route(const.Role.user)
def new_post(user: str) -> str:
    """show user's blog"""

    if current_user.username != user:  # type: ignore
        flask.abort(401)

    if current_user.blog is None:  # type: ignore
        flask.abort(404)

    return flask.render_template("blog_new.j2", c=util.jscaptcha())


@blog.post("/@<string:user>/~new")
@util.captcha
@util.require_role_route(const.Role.user)
def new_post_create(user: str) -> Response:
    """show user's blog"""

    if current_user.username != user or current_user.blog is None:  # type: ignore
        flask.abort(401)

    if current_user.blog is None:  # type: ignore
        flask.abort(404)

    title: t.Optional[str] = flask.request.form.get("title")
    content: t.Optional[str] = flask.request.form.get("content")
    keywords: t.Optional[str] = flask.request.form.get("keywords")
    description: t.Optional[str] = flask.request.form.get("description")

    if title is None or content is None or keywords is None or description is None:
        flask.abort(400)

    try:
        current_user.blog.posts.append(  # type: ignore
            post := models.BlogPost(
                title,
                keywords,
                content,
                description,
                current_user.username,  # type: ignore
            )
        )

        models.db.session.commit()
    except Exception:
        flask.flash(f"failed to post {title!r}")
        flask.abort(400)

    return flask.redirect(flask.url_for("blog.show_post", user=user, slug=post.slug))


@blog.post("/@<string:user>/~new/preview")
@util.require_role_route(const.Role.user)
def new_post_preview(user: str) -> str:
    """show user's blog"""

    if current_user.username != user:  # type: ignore
        flask.abort(401)

    blog: t.Optional[models.Blog] = current_user.blog  # type: ignore

    if blog is None:
        flask.abort(404)

    cache.blog_set(
        user,
        "post",
        flask.render_template(
            "blog_post.j2",
            blog=blog,
            post=models.BlogPost(
                flask.request.form.get("title") or "",
                "",
                flask.request.form.get("content") or "",
                "",
                current_user.username,  # type: ignore
            ),
            style=blog.style or "",  # type: ignore
        ),
    )

    return flask.jsonify(["post"])  # type: ignore


@blog.get("/@<string:user>/~style")
@util.require_role_route(const.Role.user)
def style_blog(user: str) -> str:
    """style user's blog"""

    if current_user.username != user:  # type: ignore
        flask.abort(401)

    if current_user.blog is None:  # type: ignore
        flask.abort(404)

    return flask.render_template(
        "blog_style.j2",
        c=util.jscaptcha(),
        mblog=current_user.blog,  # type: ignore
    )


@blog.post("/@<string:user>/~style")
@util.captcha
@util.require_role_route(const.Role.user)
def style_blog_save(user: str) -> Response:
    """style user's blog"""

    if current_user.username != user:  # type: ignore
        flask.abort(401)

    if current_user.blog is None:  # type: ignore
        flask.abort(404)

    try:
        current_user.blog.set_style(flask.request.form.get("css"))  # type: ignore
        models.db.session.commit()
    except Exception as e:
        flask.current_app.log_exception(e)
        flask.flash("failed to create blog, bad request", "error")
        flask.abort(400)

    return flask.redirect(flask.url_for("blog.style_blog", user=user))


@blog.post("/@<string:user>/~style/preview")
@util.require_role_route(const.Role.user)
def preview_style_index(user: str) -> flask.Response:
    """preview style user's blog"""

    if current_user.username != user:  # type: ignore
        flask.abort(401)

    if current_user.blog is None:  # type: ignore
        flask.abort(404)

    cache.blog_set(
        user,
        "blog",
        flask.render_template(
            "blog.j2",
            c=util.jscaptcha(),
            style=(flask.request.form.get("style") or "").split(
                const.BLOG_POST_SECTION_DELIM,
                1,
            )[0],
            blog=current_user.blog,  # type: ignore
            posts=models.BlogPost.query.filter_by(username=user)
            .order_by(models.BlogPost.posted.desc())  # type: ignore
            .all(),
        ),
    )

    cache.blog_set(
        user,
        "post",
        flask.render_template(
            "blog_post.j2",
            c=util.jscaptcha(),
            style=(flask.request.form.get("style") or "").replace(
                const.BLOG_POST_SECTION_DELIM,
                "",
                1,
            ),
            blog=current_user.blog,  # type: ignore
            post=models.BlogPost(
                "title",
                "",
                "minimal post content !\n\nhow are `you` ?"
                if "minimal" in flask.request.args
                else const.EXAMPLE_MARKDOWN,
                "",
                current_user.username,  # type: ignore
            ),
        ),
    )

    return flask.jsonify(["blog", "post"])  # type: ignore


@blog.get("/@<string:user>/~nuke")
@util.require_role_route(const.Role.user)
def nuke(user: str) -> str:
    """nuke blog"""

    if current_user.username != user:  # type: ignore
        flask.abort(401)

    if current_user.blog is None:  # type: ignore
        flask.abort(404)

    flask.flash("you are about to delete your blog", "warning")
    return flask.render_template("delete.j2", c=util.jscaptcha())


@blog.post("/@<string:user>/~nuke")
@util.captcha
@util.require_role_route(const.Role.user)
def nuke_commit(user: str) -> Response:
    """nuke blog"""

    if current_user.username != user:  # type: ignore
        flask.abort(401)

    if current_user.blog is None:  # type: ignore
        flask.abort(404)

    sure: t.Optional[str] = flask.request.form.get("sure")
    pin: t.Optional[str] = flask.request.form.get("pin")

    if not util.is_admin() and not (sure and current_user.blog and current_user.verify_pin(pin)):  # type: ignore
        flask.flash("blog not deleted", "info")
        return flask.redirect(flask.url_for("blog.index"))

    if not current_user.blog.delete_blog():  # type: ignore
        flask.flash("failed to delete blog", "error")
        flask.abort(500)

    flask.flash("blog deleted", "info")

    return flask.redirect(flask.url_for("blog.index"))


@blog.get("/@<string:user>/<string:slug>/~delete")
@util.require_role_route(const.Role.user)
def delete_post(user: str, slug: str) -> str:
    """delete blog post"""

    if current_user.username != user:  # type: ignore
        flask.abort(401)

    if current_user.blog is None:  # type: ignore
        flask.abort(404)

    post: models.BlogPost = models.BlogPost.query.filter_by(
        username=user, slug=slug
    ).first_or_404()

    flask.flash(f"you are about to delete your blog post {post.title!r}", "warning")
    return flask.render_template("delete.j2", c=util.jscaptcha())


@blog.post("/@<string:user>/<string:slug>/~delete")
@util.captcha
@util.require_role_route(const.Role.user)
def delete_post_commit(user: str, slug: str) -> Response:
    """delete blog post"""

    if current_user.username != user:  # type: ignore
        flask.abort(401)

    if current_user.blog is None:  # type: ignore
        flask.abort(404)

    sure: t.Optional[str] = flask.request.form.get("sure")
    pin: t.Optional[str] = flask.request.form.get("pin")

    if not util.is_admin() and not (sure and current_user.blog and current_user.verify_pin(pin)):  # type: ignore
        flask.flash("blog not deleted", "info")
        return flask.redirect(flask.url_for("blog.index"))

    if not models.BlogPost.query.filter_by(username=user, slug=slug).first_or_404().delete_post():  # type: ignore
        flask.flash("failed to delete blog post", "error")
        flask.abort(500)

    flask.flash("blog post deleted", "info")

    return flask.redirect(flask.url_for("blog.index"))


@blog.get("/@<string:user>/<string:slug>/~edit")
@util.require_role_route(const.Role.user)
def edit_post(user: str, slug: str) -> str:
    """show user's blog"""

    if current_user.username != user:  # type: ignore
        flask.abort(401)

    if current_user.blog is None:  # type: ignore
        flask.abort(404)

    return flask.render_template(
        "blog_new.j2",
        c=util.jscaptcha(),
        post=models.BlogPost.query.filter_by(username=user, slug=slug).first_or_404(),
    )


@blog.post("/@<string:user>/<string:slug>/~edit")
@util.captcha
@util.require_role_route(const.Role.user)
def edit_post_commit(user: str, slug: str) -> Response:
    """edit user's post"""

    if current_user.username != user:  # type: ignore
        flask.abort(401)

    if current_user.blog is None:  # type: ignore
        flask.abort(404)

    title: t.Optional[str] = flask.request.form.get("title")
    content: t.Optional[str] = flask.request.form.get("content")
    keywords: t.Optional[str] = flask.request.form.get("keywords")
    description: t.Optional[str] = flask.request.form.get("description")

    post: models.BlogPost = models.BlogPost.query.filter_by(
        username=user, slug=slug
    ).first_or_404()

    if title is not None:
        post.set_title(title)

    if content is not None:
        post.set_content(content)

    if keywords is not None:
        post.set_keywords(keywords)

    if description is not None:
        post.set_description(description)

    try:
        post.edited = datetime.utcnow()  # type: ignore
        models.db.session.commit()
    except Exception:
        flask.flash("failed to edit blog post", "error")
        flask.abort(500)

    return flask.redirect(flask.url_for("blog.show_post", user=user, slug=slug))


@blog.post("/@<string:user>/<string:slug>/~edit/preview")
@util.require_role_route(const.Role.user)
def edit_post_preview(user: str, slug: str) -> Response:
    """edit post preview"""

    if current_user.username != user:  # type: ignore
        flask.abort(401)

    if current_user.blog is None:  # type: ignore
        flask.abort(404)

    del slug

    return new_post_preview(user)
