"""
Reports sent by browsers through the Reporting API.

See https://developer.mozilla.org/en-US/docs/Web/API/Reporting_API and
https://w3c.github.io/webappsec-permissions-policy/#reporting
"""

from typing import Annotated, Literal
from urllib.parse import urlsplit

import msgspec

# Generous limits, browsers stay well within them; reports exceeding them are
# rejected rather than logged
FeatureName = Annotated[str, msgspec.Meta(max_length=64)]
Url = Annotated[str, msgspec.Meta(max_length=4096)]
Text = Annotated[str, msgspec.Meta(max_length=1024)]


class PermissionsPolicyViolationBody(msgspec.Struct, rename="camel"):
    """
    The `body` of a Permissions Policy violation report.

    See https://w3c.github.io/webappsec-permissions-policy/#reporting
    """

    # the spec names this `featureId`, but Chrome sends `policyId`
    feature_id: FeatureName | None = None
    policy_id: FeatureName | None = None
    disposition: Literal["enforce", "report"] | None = None
    source_file: Url | None = None
    line_number: int | None = None
    column_number: int | None = None

    def __post_init__(self):
        if not self.feature:
            raise ValueError("Object missing required field `featureId` or `policyId`")

        if self.source_file is not None:
            # reject URLs that cannot be parsed, e.g. "http://[" raises a ValueError
            urlsplit(self.source_file)

    @property
    def feature(self) -> str | None:
        return self.feature_id or self.policy_id


class _PermissionsPolicyReport(msgspec.Struct, tag_field="type"):
    """
    A single report, the `type` field determines the concrete class.

    See https://developer.mozilla.org/en-US/docs/Web/API/Report
    """

    url: Url
    body: PermissionsPolicyViolationBody
    user_agent: Text | None = None

    def __post_init__(self):
        # reject URLs that cannot be parsed, e.g. "http://[" raises a ValueError
        urlsplit(self.url)

    @property
    def type(self) -> str:
        return self.__struct_config__.tag


class PermissionsPolicyViolationReport(
    _PermissionsPolicyReport, tag="permissions-policy-violation"
):
    """
    A document used a feature the policy does not allow.

    See https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Permissions-Policy
    """


class PotentialPermissionsPolicyViolationReport(
    _PermissionsPolicyReport, tag="potential-permissions-policy-violation"
):
    """
    An iframe requested a feature, through its `allow` attribute, the policy does
    not allow.

    See https://developer.mozilla.org/en-US/docs/Web/HTML/Element/iframe#allow
    """


PermissionsPolicyReport = (
    PermissionsPolicyViolationReport | PotentialPermissionsPolicyViolationReport
)

# A batch as sent by browsers. Each report is kept raw, to be decoded separately,
# so one report of an unknown type (e.g. a deprecation) or an invalid one does not
# reject the whole batch.
ReportBatch = list[msgspec.Raw]
