#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""constants"""

from enum import Enum, auto
from typing import Dict, Final, Tuple

PIN_LEN: Final[int] = 6
ID_LEN: Final[int] = 64
NAME_LEN: Final[int] = 256
APP_SECRET_LEN: Final[int] = 512
USERNAME_LEN: Final[int] = 256
BIO_LEN: Final[int] = 1024
COUNTER_ORIGIN_LEN: Final[int] = 512

ARGON2_SALT_LENGTH: Final[int] = 32
ARGON2_HASH_LENGTH: Final[int] = 512

HASH_LEN: Final[int] = ARGON2_SALT_LENGTH + ARGON2_HASH_LENGTH + 256

APPS_LIMIT: Final[int] = 128
COUNTERS_LIMIT: Final[int] = 128

HUGEINT_MAX: Final[int] = (10**65) - 1

BLOG_POST_SLUG_LEN: Final[int] = 128
BLOG_POST_KEYWORDS_LEN: Final[int] = 256
BLOG_POST_CONTENT_LEN: Final[int] = 14336
BLOG_POST_DESCRIPTION_LEN: Final[int] = 512

BLOG_PRIMARY_LEN: Final[int] = 7
BLOG_SECONDARY_LEN: Final[int] = 7
BLOG_LOCALE_LEN: Final[int] = 5

BLOG_COMMENT_URL_LEN: Final[int] = 196
BLOG_VISITOR_URL_LEN: Final[int] = 196

BLOG_POST_MAX: Final[int] = 1024

EXAMPLE_MARKDOWN: Final[str] = f"""
# hello world

this is my markdown :)

<#:hello world> is the top of the page

    my
    code
    int main(void) {{
        puts("hello world !");
        return 0;
    }}

- list
- two list
- three list

1. one
2. two
3. three

~~strike~~

`code` is my beloved :)

> quoting quotes
> quoting quotes
> aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa

{'longword' * 20}

{'long text ' * 20}

# h1 ( h2 )
## h2
### h3
#### h4
##### h5
###### h6

epic stuff

*italic* **bold** ***bold italic***
""".strip()

BLOG_POST_SECTION_DELIM: Final[str] = "!!!section:[post]:"

CONTEXT_WORDS: Tuple[str, ...] = (
    "the",
    "a",
    "about",
    "etc",
    "on",
    "at",
    "in",
    "by",
    "its",
    "i",
    "to",
    "my",
    "of",
    "between",
    "because",
    "of",
    "or",
    "how",
    "to",
    "begin",
    "is",
    "this",
    "person",
    "important",
    "homework",
    "and",
    "cause",
    "how",
    "what",
    "for",
    "with",
    "without",
    "using",
    "im",
)


class Role(Enum):
    """user roles

    users manage their usage of resources and their posted content, and are the highest level contributors
    trusted users manage their content and worry less about usage
    moderators manage their content and others' content
    administrators manage their content, others' content and users' accounts
    owners manage their content, others' content and users' accounts, backend, system administration and are the lowest level contributors
    """

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
