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

KDF_PASSES: int = 128000
KEY_SIZE: int = 32


def derive_key(password: bytes, salt: bytes) -> bytes:
    """derive key"""
    return PBKDF2HMAC(
        algorithm=HASH_ALGO,
        length=32,
        salt=salt,
        iterations=KDF_PASSES,
        backend=DEFAULT_BACKEND,
    ).derive(password)


def encrypt_aes(data: str, password: bytes, salt: bytes) -> str:
    """aes encryption"""

    iv: bytes = RAND.randbytes(16)

    key: bytes = derive_key(password, salt)

    encryptor: CipherContext = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
        backend=DEFAULT_BACKEND,
    ).encryptor()

    padder: padding.PaddingContext = padding.PKCS7(128).padder()

    return base64.b85encode(
        iv
        + encryptor.update(padder.update(data.encode("ascii")) + padder.finalize())
        + encryptor.finalize()
    ).decode("ascii")


def decrypt_aes(data: str, password: bytes, salt: bytes) -> str:
    """aes decryption"""

    e_data: bytes = base64.b85decode(data)

    iv: bytes = e_data[:16]
    ct: bytes = e_data[16:]

    key: bytes = derive_key(password, salt)

    decryptor: CipherContext = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
        backend=DEFAULT_BACKEND,
    ).decryptor()

    pt: bytes = decryptor.update(ct) + decryptor.finalize()

    unpadder: padding.PaddingContext = padding.PKCS7(128).unpadder()

    return (unpadder.update(pt) + unpadder.finalize()).decode("ascii")
