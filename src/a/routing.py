#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""routing"""

from typing import Any

from flask import Blueprint, Response

from .const import Role
from .util import make_api, require_role_route


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

    def set_api(self) -> "Bp":
        """disable cors and cache"""

        @self.after_request  # type: ignore
        def _(response: Response) -> Response:
            """disable cache"""
            return make_api(response)

        return self
