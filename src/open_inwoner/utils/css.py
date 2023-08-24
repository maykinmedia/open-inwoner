import tinycss2

# initially copied from bleach
ALLOWED_PROPERTIES = frozenset(
    (
        # CSS properties
        #
        # "azimuth",
        "background-color",
        "border-bottom-color",
        "border-collapse",
        "border-color",
        "border-left-color",
        "border-right-color",
        "border-top-color",
        # "clear",
        "color",
        "cursor",
        # "direction",
        # "display",
        # "elevation",
        # "float",
        "font",
        "font-family",
        "font-size",
        "font-style",
        "font-variant",
        "font-weight",
        # "height",
        "letter-spacing",
        "line-height",
        # "overflow",
        # "pause",
        # "pause-after",
        # "pause-before",
        # "pitch",
        # "pitch-range",
        # "richness",
        # "speak",
        # "speak-header",
        # "speak-numeral",
        # "speak-punctuation",
        # "speech-rate",
        # "stress",
        "text-align",
        "text-decoration",
        "text-indent",
        # "unicode-bidi",
        "vertical-align",
        # "voice-family",
        # "volume",
        "white-space",
        # "width",
        #
        # SVG properties
        #
        "fill",
        "fill-opacity",
        "fill-rule",
        "stroke",
        "stroke-width",
        "stroke-linecap",
        "stroke-linejoin",
        "stroke-opacity",
    )
)


def clean_stylesheet(
    styles: str,
    allowed_properties=ALLOWED_PROPERTIES,
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
            _clean_toplevel(rule, allowed_properties)
            if rule.content:
                new_rules.append(rule)

    if not new_rules:
        return ""

    return tinycss2.serialize(new_rules).strip()


def _clean_toplevel(rule, allowed_css_properties):
    # main loop from Bleach's CSSSanitizer.sanitize_css()
    new_tokens = []

    for token in tinycss2.parse_declaration_list(rule.content):
        if token.type == "declaration":
            if token.lower_name in allowed_css_properties:
                new_tokens.append(token)
        elif token.type in ("comment", "whitespace"):
            if new_tokens and new_tokens[-1].type != token.type:
                new_tokens.append(token)

    rule.content = new_tokens
