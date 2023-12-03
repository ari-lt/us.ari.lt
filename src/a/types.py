#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""types"""

from typing import Any


class Unused:
    """unused arg"""

    def __init__(*args: Any) -> None:
        del args
