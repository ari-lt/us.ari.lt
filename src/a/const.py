#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""constants"""

from enum import Enum, auto
from typing import Dict, Final, List, Tuple

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

MARKDOWN_EXTS: Final[List[str]] = [
    "speedup",
    "strikethrough",
    "mark",
    "insert",
    "superscript",
    "subscript",
    "footnotes",
    "table",
    "url",
    "abbr",
    "def_list",
    "ruby",
    "task_lists",
    "spoiler",
]


EXAMPLE_MARKDOWN: Final[
    str
] = f"""
{'markdown test ' * 20}

{'markdowntest' * 20}

link : [i am a link](https://ari.lt/)

image : ![i am an image](https://ari.lt/favicon.ico)

link + image : [![i am an image](https://ari.lt/favicon.ico)](https://ari.lt/)

---
## headers

# h1 ( h2 )
# h2
# h3
# h4
# h5
# h6
---

## Text Styles

**bold text**

*italic text*

***bold italic***

~~{'strikethrough'}~~

`{'inline code ' * 10}`

---

## lists

* unordered list item 1
    * nested unordered list item 1
    * nested unordered list item 2
* {'unordered list item 2 ' * 10}

1. ordered list item 1
    1. nested ordered list item 1
    2. nested ordered list item 2
2. {'ordered list item 2 ' * 10}

---

## blockquotes

> this is a block quote
> this is more quoting
> even more !!

---

## code blocks

lang :

diff :
```diff
--- main.cpp    2020-09-20 19:49:29.000000000 +0100
+++ main.cpp    2020-09-20 19:51:39.000000000 +0100
@@ -1,9 +1,7 @@
 #include <iostream>

 int main() {{
-    // This comment will be deleted in the next version of the code.
-    std::cout << "Hello world!\n";
+    std::cout << "Welcome to my program!\n";
     return 0;
 }}
```

```hfiuhwuifwe
hewiuhfwe uifheiuhf we
ughfeiwuh
```

cpp :

```cpp
/* epic code */
// epic code

#ifndef _EPIC_HPP
#define _EPIC_HPP
#include <iostream>
#include <vector>
#include <string>

template <typename T> T add(T a, T b) {{ return a + b; }}

class MyClass {{
    int value;

  public:
    MyClass(int v) : value(v) {{}}

    int get_value() const {{ return value; }}

    friend std::ostream &operator<<(std::ostream &os, const MyClass &obj) {{
        os << "MyClass with value " << obj.get_value();
        return os;
    }}
}};

int main(void) {{
    std::cout << "sum of integers : " << add<int>(5, 2) << '\\n';
    std::cout << "sum of floats : " << add<float>(5.6f, 2.3f) << '\\n';

    std::string str = "hello, world !";
    std::cout << str << '\\n';

    MyClass obj1(7);
    std::cout << obj1 << '\\n';

    std::vector<MyClass> vec;
    vec.push_back(obj1);
    vec.push_back(MyClass(13));

    std::cout << "vector content :\\n";

    for (const MyClass &obj : vec)
        std::cout << " - " << obj << '\\n';

    return 0;
}}
#endif /* _EPIC_HPP */
```

no lang :

```
const hello = "hello";
if (hello)
    console.log(foo); // prints 'hello'
```

intended :

    const hello = "hello";
    if (hello)
        console.log(foo); // prints 'hello'

---

## tables

| column 1      | column 2 | column 3 |
| :------------ | :------: | -------: |
| cell          | cell     | cell     |
| cell          | cell     | cell     |
| cell          | cell     | cell     |
| {'cell' * 20} | cell     | cell     |

---

## checkbox

- [ ] unchecked
- [x] checked

---

## footnotes

here is a footnote[^1]

have another one[^here]

---

## superscript and subscript

hello~world~

hello^world^

---

## inserts

^^insert me^^

---

## abbrs

this will become HTML !

*[HTML]: hypertext markup language

---

## spoiler

>! here is the spoiler content
>!
>! it will be hidden

---

## mark

i think ==i am marking this== /shrug

---

## definitions

first term
: first definition
: second definition

second term
: third definition

---

[^1]: this is my footnote
[^here]: here it is !
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


def enum2json(enum: Enum) -> Dict[str, int]:
    """enum to json"""
    return {v.name: v.value for v in enum}  # type: ignore


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


class CodeTheme(Enum):
    none = auto()
    abap = auto()
    algol = auto()
    algol_nu = auto()
    arduino = auto()
    autumn = auto()
    borland = auto()
    bw = auto()
    coffee = auto()
    colorful = auto()
    default = auto()
    dracula = auto()
    emacs = auto()
    friendly = auto()
    friendly_grayscale = auto()
    fruity = auto()
    gh_dark = auto()
    gruvbox = auto()
    igor = auto()
    inkpot = auto()
    lightbulb = auto()
    lilypond = auto()
    lovelace = auto()
    manni = auto()
    material = auto()
    monokai = auto()
    murphy = auto()
    native = auto()
    nord = auto()
    onedark = auto()
    paraiso_dark = auto()
    paraiso_light = auto()
    pastie = auto()
    perldoc = auto()
    rainbow_dash = auto()
    rrt = auto()
    sas = auto()
    solarized = auto()
    staroffice = auto()
    stata_dark = auto()
    stata_light = auto()
    tango = auto()
    trac = auto()
    vim = auto()
    vs = auto()
    xcode = auto()
    zenburn = auto()
