#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""constants"""

from enum import Enum, auto
from typing import Dict, Final

PIN_LEN: Final[int] = 6
ID_LEN: Final[int] = 64
NAME_LEN: Final[int] = 256
APP_SECRET_LEN: Final[int] = 512
USERNAME_LEN: Final[int] = 256
BIO_LEN: Final[int] = 1024
COUNTER_ORIGINS_LEN: Final[int] = 512

ARGON2_SALT_LENGTH: Final[int] = 32
ARGON2_HASH_LENGTH: Final[int] = 512

HASH_LEN: Final[int] = ARGON2_SALT_LENGTH + ARGON2_HASH_LENGTH + 256

APPS_LIMIT: Final[int] = 128
COUNTERS_LIMIT: Final[int] = 128

HUGEINT_MAX: Final[int] = (10**65) - 1


class Role(Enum):
    """user roles

    users manage their usage of resources and their posted content, and are the highest level contributors
    trusted users manage their content and worry less about usage
    moderators manage their content and others' content
    administrators manage their content, others' content and users' accounts
    owners manage their content, others' content and users' accounts, backend, system administration and are the lowest level contributors"""

    user = auto()
    trusted = auto()
    mod = auto()
    admin = auto()
    owner = auto()

    @classmethod
    def json(cls) -> Dict[str, int]:
        """roles as json"""

        return {
            "user": cls.user.value,
            "trusted": cls.trusted.value,
            "mod": cls.mod.value,
            "admin": cls.admin.value,
            "owner": cls.owner.value,
        }
