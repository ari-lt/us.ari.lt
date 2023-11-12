#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""a.ari-web.xyz"""

import os
import sys
from typing import NoReturn

from flask import Flask

from a import create_app


def err(msg: str) -> NoReturn:
    """error"""
    print(msg, file=sys.stderr)
    sys.exit(1)


if (maria_user := os.environ.get("MARIA_USER")) is None:
    err("no MARIA_USER defined")

if (maria_pass := os.environ.get("MARIA_PASS")) is None:
    err("no MARIA_PASS defined")


app: Flask = create_app(maria_user, maria_pass)


def main() -> int:
    """entry/main function"""

    app.run("127.0.0.1", 8080, True, threaded=True)

    return 0


if __name__ == "__main__":
    assert main.__annotations__.get("return") is int, "main() should return an integer"
    raise SystemExit(main())
