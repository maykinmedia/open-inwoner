def middle_truncate(value: str, length: int, dots="...") -> str:
    if len(value) <= length:
        return value
    half = int(length / 2)
    return f"{value[: half - len(dots)]}{dots}{value[-half:]}"
