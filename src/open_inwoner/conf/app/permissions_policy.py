from maykin_common.config import DocumentationParams, config

#
# django-permissions-policy
#
# Browser features are denied unless explicitly needed. Note that the policy is
# evaluated against the *document* origin, so third-party scripts running in our
# pages are covered by "self"; only cross-origin iframes need to be listed
# explicitly.
#
_EMBEDDED_VIDEO_ORIGINS = ["https://www.youtube.com", "https://player.vimeo.com"]

_permissions_policy = {
    # Delegated to the YouTube/Vimeo iframes of the CMS videoplayer plugin, which
    # request these through their `allow` attribute.
    "autoplay": ["self", *_EMBEDDED_VIDEO_ORIGINS],
    "fullscreen": ["self", *_EMBEDDED_VIDEO_ORIGINS],
    # WebAuthn is used for two-factor authentication in the admin
    "publickey-credentials-create": "self",
    "publickey-credentials-get": "self",
    "clipboard-write": "self",
    # Not used anywhere
    "accelerometer": [],
    "ambient-light-sensor": [],
    "bluetooth": [],
    "browsing-topics": [],
    "camera": [],
    "captured-surface-control": [],
    "clipboard-read": [],
    "compute-pressure": [],
    "digital-credentials-get": [],
    "display-capture": [],
    "encrypted-media": [],
    "gamepad": [],
    "geolocation": [],
    "gyroscope": [],
    "hid": [],
    "identity-credentials-get": [],
    "idle-detection": [],
    "local-fonts": [],
    "magnetometer": [],
    "microphone": [],
    "midi": [],
    "otp-credentials": [],
    "payment": [],
    "picture-in-picture": [],
    "screen-wake-lock": [],
    "serial": [],
    "storage-access": [],
    "usb": [],
    "web-share": [],
    "window-management": [],
    "xr-spatial-tracking": [],
}

_permissions_policy_report_only = config(
    "PERMISSIONS_POLICY_REPORT_ONLY",
    default=False,
    documentation=DocumentationParams(
        help_text=(
            "When enabled, the Permissions Policy is applied in report-only mode: "
            "violations are reported but not blocked. Use only for testing a new policy; "
            "disables enforcement while active."
        ),
        group="Security",
    ),
)
if _permissions_policy_report_only:
    PERMISSIONS_POLICY = {}
    PERMISSIONS_POLICY_REPORT_ONLY = _permissions_policy
else:
    PERMISSIONS_POLICY = _permissions_policy
    PERMISSIONS_POLICY_REPORT_ONLY = {}
