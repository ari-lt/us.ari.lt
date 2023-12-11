#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""markdown"""

import re
import string
import typing as t
from functools import lru_cache

import mistune
import unidecode
from pygments import highlight  # type: ignore
from pygments.formatters import html
from pygments.lexers import get_lexer_by_name
from pygments.style import Style
from pygments.token import (Comment, Error, Generic, Keyword, Literal, Name,
                            Number, Operator, Punctuation, String, Token)
from web_mini.css import minify_css

from .const import BLOG_POST_SLUG_LEN, CONTEXT_WORDS, MARKDOWN_EXTS, CodeTheme

TITLE_LINKS_RE: t.Final[str] = r"<#:[^>]+?>"


class CoffeeStyle(Style):
    """
    A warm and cozy theme based off gruvbox
    https://github.com/pygments/pygments/pull/2609
    """

    background_color = "#262220"
    highlight_color = "#ddd0c0"

    line_number_color = "#4e4e4e"
    line_number_special_color = "#8f9494"

    styles = {
        Comment: "#70757A",
        Comment.Hashbang: "#8f9f9f",
        Comment.Preproc: "#fdd0c0",
        Comment.PreprocFile: "#c9b98f",
        Comment.Special: "#af5f5f",
        Error: "#af5f5f",
        Generic.Deleted: "#bb6868",
        Generic.Emph: "italic",
        Generic.Error: "#af5f5f",
        Generic.Inserted: "#849155",
        Generic.Output: "#ddd0c0",
        Generic.Strong: "bold",
        Generic.Traceback: "#af5f5f",
        Keyword: "#919191",
        Keyword.Constant: "#875f5f",
        Keyword.Declaration: "#875f5f",
        Keyword.Namespace: "#875f5f",
        Keyword.Reserved: "#b46276",
        Keyword.Type: "#af875f",
        Literal: "#af875f",
        Name: "#ddd0c0",
        Name.Attribute: "#ddd0c0",
        Name.Builtin: "#ddd0c0",
        Name.Builtin.Pseudo: "#87afaf",
        Name.Class: "#875f5f",
        Name.Constant: "#af8787",
        Name.Decorator: "#fdd0c0",
        Name.Entity: "#ddd0c0",
        Name.Exception: "#877575",
        Name.Function: "#fdd0c0",
        Name.Function.Magic: "#fdd0c0",
        Name.Other: "#ddd0c0",
        Name.Property: "#dfaf87",
        Name.Tag: "#87afaf",
        Name.Variable: "#ddd0c0",
        Number: "#87afaf",
        Operator: "#878787",
        Operator.Word: "#878787",
        Punctuation: "#ddd0c0",
        String: "#c9b98f",
        String.Affix: "#dfaf87",
        String.Doc: "#878787",
        String.Escape: "#af5f5f",
        String.Interpol: "#af5f5f",
        String.Other: "#fdd0c0",
        String.Regex: "#af5f5f",
        String.Symbol: "#af5f5f",
        Token: "#ddd0c0",
    }


def slugify(
    title: str, wl: int = 10, ll: int = BLOG_POST_SLUG_LEN, prefix: str = ""
) -> str:
    """slugify a title"""

    return (
        "-".join(
            ([prefix] if prefix else [])
            + [
                w
                for w in "".join(
                    c
                    for c in unidecode.unidecode(title).lower()
                    if c not in string.punctuation
                ).split()
                if w not in (CONTEXT_WORDS or [])
            ][:wl]
        )[:ll].strip("-")
        or "post"
    )


def parse_inline_titlelink(
    _: mistune.inline_parser.InlineParser,
    m: re.Match[str],
    state: mistune.core.InlineState,
) -> int:
    text: str = m.group(0)[3:-1]

    state.append_token(
        {
            "type": "link",
            "children": [{"type": "text", "raw": f"# {mistune.escape(text)}"}],
            "attrs": {"url": f"#{slugify(text, 768, 768)}"},
        }
    )

    return m.end()


def titlelink(md: mistune.Markdown) -> None:
    md.inline.register("titlelink", TITLE_LINKS_RE, parse_inline_titlelink, before="link")  # type: ignore


class BlogRenderer(mistune.HTMLRenderer):
    def heading(self, text: str, level: int, **_: t.Any) -> str:
        slug: str = slugify(text, 768, 768)
        level = max(2, level)

        return f'<h{level} id="{slug}" h><a href="#{slug}">#</a> {mistune.escape(text)}</h{level}>'

    def block_code(self, code: str, info: t.Optional[str] = None) -> str:
        if info:
            try:
                return highlight(code, get_lexer_by_name(info, stripall=True), html.HtmlFormatter())  # type: ignore
            except Exception:
                return self.block_code(code)

        return "<pre><code>" + mistune.escape(code) + "</code></pre>"


def markdown(md: str) -> str:
    return mistune.create_markdown(  # type: ignore
        plugins=MARKDOWN_EXTS + [titlelink],
        renderer=BlogRenderer(),  # type: ignore
    )(md)


@lru_cache
def get_code_style(style: CodeTheme) -> str:
    """get code style"""

    if style == CodeTheme.none:
        return ""

    return minify_css(
        html.HtmlFormatter(  # type: ignore
            cssclass="highlight",
            style=CoffeeStyle if style == CodeTheme.coffee else style.name,
        ).get_style_defs()
    )
