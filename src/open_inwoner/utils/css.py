from typing import List

import tinycss2
from bleach.css_sanitizer import (
    ALLOWED_CSS_PROPERTIES as _ALLOWED_CSS_PROPERTIES,
    ALLOWED_SVG_PROPERTIES as _ALLOWED_SVG_PROPERTIES,
)

# alias for clarity / override
ALLOWED_CSS_PROPERTIES = _ALLOWED_CSS_PROPERTIES
ALLOWED_SVG_PROPERTIES = _ALLOWED_SVG_PROPERTIES


def allowed_properties() -> List[str]:
    # used for admin etc
    parts = set()
    parts.update(ALLOWED_CSS_PROPERTIES)
    parts.update(ALLOWED_SVG_PROPERTIES)
    return list(sorted(parts))


def clean_stylesheet(
    styles: str,
    allowed_css_properties=ALLOWED_CSS_PROPERTIES,
    allowed_svg_properties=ALLOWED_SVG_PROPERTIES,
) -> str:
    """Apply Bleach style CSS filtering on whole stylesheet"""

    rules = tinycss2.parse_stylesheet(
        styles, skip_whitespace=False, skip_comments=False
    )

    if not rules:
        return ""

    new_rules = []
    for rule in rules:
        if rule.type == "qualified-rule":
            _clean_toplevel(rule, allowed_css_properties, allowed_svg_properties)
            if rule.content:
                new_rules.append(rule)

    if not new_rules:
        return ""

    return tinycss2.serialize(new_rules).strip()


def _clean_toplevel(rule, allowed_css_properties, allowed_svg_properties):
    # main loop from Bleach's CSSSanitizer.sanitize_css()
    new_tokens = []

    for token in tinycss2.parse_declaration_list(rule.content):
        if token.type == "declaration":
            if (
                token.lower_name in allowed_css_properties
                or token.lower_name in allowed_svg_properties
            ):
                new_tokens.append(token)
        elif token.type in ("comment", "whitespace"):
            if new_tokens and new_tokens[-1].type != token.type:
                new_tokens.append(token)

    rule.content = new_tokens
