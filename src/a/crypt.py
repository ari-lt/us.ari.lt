#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cryptography"""

import base64
import secrets
import typing as t

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import (Cipher, CipherContext,
                                                    algorithms, modes)
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

RAND: secrets.SystemRandom = secrets.SystemRandom()
DEFAULT_BACKEND: t.Final[t.Any] = default_backend()

HASH_ALGO: hashes.HashAlgorithm = hashes.SHA3_512()
KDF_PASSES: int = 96000


def encrypt_aes(
    data: str,
    password: bytes,
    salt: str,
) -> str:
    """aes encryption"""

    key: bytes = PBKDF2HMAC(
        algorithm=HASH_ALGO,
        length=32,
        salt=base64.b85decode(salt.encode("ascii")),
        iterations=KDF_PASSES,
        backend=DEFAULT_BACKEND,
    ).derive(password)

    iv: bytes = RAND.randbytes(16)

    encryptor: CipherContext = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
        backend=DEFAULT_BACKEND,
    ).encryptor()

    padder: padding.PaddingContext = padding.PKCS7(128).padder()

    enc_data: bytes = (
        iv
        + encryptor.update(padder.update(data.encode("ascii")) + padder.finalize())
        + encryptor.finalize()
    )

    return base64.b85encode(enc_data).decode("ascii")


def decrypt_aes(
    data: str,
    password: bytes,
    salt: str,
) -> str:
    """aes decryption"""

    enc_data: bytes = base64.b85decode(data.encode("ascii"))

    key: bytes = PBKDF2HMAC(
        algorithm=HASH_ALGO,
        length=32,
        salt=base64.b85decode(salt.encode("ascii")),
        iterations=KDF_PASSES,
        backend=DEFAULT_BACKEND,
    ).derive(password)

    iv: bytes = enc_data[:16]

    decryptor: CipherContext = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
        backend=DEFAULT_BACKEND,
    ).decryptor()

    unpadder: padding.PaddingContext = padding.PKCS7(128).unpadder()

    dec_data: bytes = (
        unpadder.update(decryptor.update(enc_data[16:]) + decryptor.finalize())
        + unpadder.finalize()
    )

    return dec_data.decode("ascii")
