#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""captcha"""

from base64 import b64encode
from io import BytesIO

import flask_ishuman
from pydub import AudioSegment  # type: ignore

c: flask_ishuman.IsHuman = flask_ishuman.IsHuman()


def audio(gen: flask_ishuman.CaptchaGenerator) -> str:
    """generate ogg audio"""

    ogg: BytesIO = BytesIO()
    AudioSegment.from_wav(BytesIO(gen.rawwav())).export(ogg, format="ogg")  # type: ignore

    return f'<audio id=audio-captcha controls> \
<source src="data:audio/ogg;base64,{b64encode(ogg.read()).decode("ascii")}" type=audio/ogg /> Audio CAPTCHA </audio>'


class OggCaptchaGenerator(flask_ishuman.CaptchaGenerator):
    """a custom CaptchaGenerator using the ogg format rather than wav"""

    def audio(self, *_) -> str:
        """gen audio captcha ( custom )"""
        return audio(self)

    @classmethod
    def from_gen(cls, gen: flask_ishuman.CaptchaGenerator) -> "OggCaptchaGenerator":
        """create OggCaptchaGenerator from CaptchaGenerator"""
        return cls(gen.code, gen.cimage, gen.caudio)
