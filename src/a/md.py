#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""markdown"""

import re
import string
import typing as t

import mistune
import unidecode

from .const import BLOG_POST_SLUG_LEN, CONTEXT_WORDS

TITLE_LINKS_RE: t.Final[str] = r"<#:[^>]+?>"


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
            "children": [{"type": "text", "raw": f"# {text}"}],
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

        return f'<h{level} id="{slug}" h><a href="#{slug}">#</a> {text}</h{level}>'


def markdown(md: str) -> str:
    return mistune.create_markdown(  # type: ignore
        plugins=[
            "speedup",
            "strikethrough",
            "insert",
            "superscript",
            "subscript",
            "footnotes",
            "abbr",
            titlelink,
        ],
        renderer=BlogRenderer(),  # type: ignore
    )(md)
