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


def pyhash_value(value) -> int:
    """
    Best effort to create a python hash() of common types, even for lists, tuples and dictionaries.

    Use with care as source is still mutable.

    Example use-case is generating a cache-key from arguments to store (API) result in a dict.
    """
    try:
        # every normal hashable
        return hash(value)

    except TypeError as e:
        if isinstance(value, dict):
            # convert dict to hashable tuple of key-value tuples
            # sort the *hashed* keys to support mixed key types
            elems = sorted(
                ((pyhash_value(k), pyhash_value(v)) for k, v in value.items())
            )
            return hash(tuple(elems))
        elif isinstance(value, (list, tuple)):
            # convert list to hashable tuple
            return hash(tuple(map(pyhash_value, value)))
        elif isinstance(value, set):
            # convert set to sorted hashable tuple
            # sort *hashes* to support mixed value types
            return hash(tuple(sorted(map(pyhash_value, value))))
        else:
            # we could add more support (dataclasses), but for now lets reraise
            raise TypeError(
                f"unhashable type '{type(value)}' for value '{value}'"
            ) from e
