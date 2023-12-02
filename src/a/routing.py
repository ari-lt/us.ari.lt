#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""routing"""

from typing import Any

from flask import Blueprint

from .const import Role
from .util import require_role_route


class Bp(Blueprint):
    def get(self, rule: str, **kwargs: Any) -> Any:
        """wrapper for GET"""
        return self.route(rule=rule, methods=("GET",), **kwargs)

    def post(self, rule: str, **kwargs: Any) -> Any:
        """wrapper for POST"""
        return self.route(rule=rule, methods=("POST",), **kwargs)

    def set_role(self, role: Role) -> "Bp":
        """disallow users to access this under the role `role`"""

        @self.before_request  # type: ignore
        @require_role_route(role)
        def _() -> None:
            pass

        return self
