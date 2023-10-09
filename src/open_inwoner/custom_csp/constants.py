from django.db import models


class CSPDirective(models.TextChoices):
    # via https://django-csp.readthedocs.io/en/latest/configuration.html
    DEFAULT_SRC = "default-src", "default-src"
    SCRIPT_SRC = "script-src", "script-src"
    SCRIPT_SRC_ATTR = "script-src-attr", "script-src-attr"
    SCRIPT_SRC_ELEM = "script-src-elem", "script-src-elem"
    IMG_SRC = "img-src", "img-src"
    OBJECT_SRC = "object-src", "object-src"
    PREFETCH_SRC = "prefetch-src", "prefetch-src"
    MEDIA_SRC = "media-src", "media-src"
    FRAME_SRC = "frame-src", "frame-src"
    FONT_SRC = "font-src", "font-src"
    CONNECT_SRC = "connect-src", "connect-src"
    STYLE_SRC = "style-src", "style-src"
    STYLE_SRC_ATTR = "style-src-attr", "style-src-attr"
    STYLE_SRC_ELEM = "style-src-elem", "style-src-elem"
    BASE_URI = (
        "base-uri",
        "base-uri",
    )  # Note: This doesn’t use default-src as a fall-back
    CHILD_SRC = (
        "child-src",
        "child-src",
    )  # Note: This doesn’t use default-src as a fall-back
    FRAME_ANCESTORS = (
        "frame-ancestors",
        "frame-ancestors",
    )  # Note: This doesn’t use default-src as a fall-back
    NAVIGATE_TO = (
        "navigate-to",
        "navigate-to",
    )  # Note: This doesn’t use default-src as a fall-back
    FORM_ACTION = (
        "form-action",
        "form-action",
    )  # Note: This doesn’t use default-src as a fall-back
    SANDBOX = "sandbox", "sandbox"  # Note: This doesn’t use default-src as a fall-back
    REPORT_URI = (
        "report-uri",
        "report-uri",
    )  # Note: This doesn’t use default-src as a fall-back
    REPORT_TO = "report-to", "report-to"
    MANIFEST_SRC = "manifest-src", "manifest-src"
    WORKER_SRC = "worker-src", "worker-src"
    PLUGIN_TYPES = "plugin-types", "plugin-types"
    REQUIRE_SRI_FOR = "require-sri-for", "require-sri-for"
