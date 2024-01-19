from hashlib import md5, sha256
from typing import Optional


def generate_email_from_string(
    value: str, domain: Optional[str] = "example.org"
) -> str:
    """generate email address based on string"""
    salt = "generate_email_from_bsn"
    hashed_bsn = md5((salt + value).encode(), usedforsecurity=False).hexdigest()
    return f"{hashed_bsn}@{domain}"


def create_sha256_hash(val, salt=None):
    """
    Creates a hashed value using sha256 and a custom salt, provided by Django's ``settings.SECRET_KEY``.

    :param val: The value to hash.
    :return: The hashed value.
    """

    # Consistently encode strings as utf-8.
    if isinstance(val, str):
        val = val.encode("utf-8")

    h = sha256(val)
    h.update(salt.encode("utf-8"))
    return h.hexdigest()
