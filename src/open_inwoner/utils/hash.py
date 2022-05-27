from hashlib import md5


def generate_email_from_string(value: str) -> str:
    """generate email address based on string"""
    hashed_bsn = md5(value.encode()).hexdigest()

    return f"{hashed_bsn}@example.org"
