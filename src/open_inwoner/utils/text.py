import functools

from django.utils.encoding import force_str
from django.utils.html import conditional_escape, format_html


def middle_truncate(value: str, length: int, dots="...") -> str:
    if len(value) <= length:
        return value
    half = int(length / 2)
    return f"{value[: half - len(dots)]}{dots}{value[-half:]}"


def html_tag_wrap_format(format_str: str, tag: str, **kwargs) -> str:
    if not kwargs:
        raise ValueError("expected replacement kwargs")
    html_tag = "<{}>{{}}</{}>".format(tag, tag)
    replace = {
        name: format_html(html_tag, force_str(value)) for name, value in kwargs.items()
    }
    text = conditional_escape(format_str)
    return format_html(text, **replace)


def mask_sensitive_data(value, visible_start=2, visible_end=2, min_length=6):
    """
    Masks a sensitive string value but keeps some identifying characters.
    Always ensures at least one character is masked if the string is long enough.

    Args:
        value: The string to mask
        visible_start: Number of characters to show at the beginning
        visible_end: Number of characters to show at the end
        min_length: Minimum length required to apply partial masking

    Returns:
        Masked string
    """
    if not value:
        return ""

    value = str(value)
    length = len(value)

    # Return fully masked if shorter than minimum length
    if length < min_length:
        return "*" * length

    # Adjust visible parameters to ensure at least one character is masked
    # when the string is long enough
    if visible_start + visible_end >= length:
        # If showing all chars, reduce to show at most length-1 chars
        total_visible = length - 1

        # Distribute the reduction proportionally if possible
        if visible_start > 0 and visible_end > 0:
            visible_start = max(
                1, int(visible_start * total_visible / (visible_start + visible_end))
            )
            visible_end = total_visible - visible_start
        elif visible_start > 0:
            visible_start = total_visible
            visible_end = 0
        else:
            visible_start = 0
            visible_end = total_visible

    # Calculate how many characters to mask
    mask_length = length - visible_start - visible_end

    # Create the masked string
    return (
        value[:visible_start] + "*" * mask_length + value[-visible_end:]
        if visible_end > 0
        else value[:visible_start] + "*" * mask_length
    )


mask_phone_number = functools.partial(
    mask_sensitive_data, visible_start=2, visible_end=2, min_length=8
)
