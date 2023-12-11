#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cache"""

from time import sleep
from typing import Optional

from flask_caching import Cache

blog: Cache = Cache()


def blog_set(user: str, ctx: str, data: str) -> None:
    """creates a blog cache"""
    try:
        blog.set(f"{user}_{ctx}", data)  # type: ignore
    except Exception:
        sleep(0.5)
        return blog_set(user, ctx, data)


def blog_get(user: str, ctx: str) -> Optional[str]:
    """does blog cache have this users context"""
    try:
        return blog.get(f"{user}_{ctx}")  # type: ignore
    except Exception:
        sleep(0.5)
        return blog_get(user, ctx)
