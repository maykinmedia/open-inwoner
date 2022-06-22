from hashlib import md5


def generate_email_from_string(value: str) -> str:
    """generate email address based on string"""
    salt = "generate_email_from_bsn"
    hashed_bsn = md5((salt + value).encode(), usedforsecurity=False).hexdigest()

    return f"{hashed_bsn}@example.org"
