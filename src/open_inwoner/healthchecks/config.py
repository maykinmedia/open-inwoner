from typing import TypedDict

from django.conf import settings


class HealthChecksConfig(TypedDict):
    """Health checks configuration structure."""

    readiness_checks: list[str]
    startup_checks: list[str]
    liveness_checks: list[str]
    verbose_response: bool


# Default health check configurations
DEFAULT_READINESS_CHECKS = [
    "open_inwoner.healthchecks.checks.check_database",
    "open_inwoner.healthchecks.checks.check_cache",
]

DEFAULT_STARTUP_CHECKS = [
    "open_inwoner.healthchecks.checks.check_database",
]

DEFAULT_LIVENESS_CHECKS: list[str] = []

DEFAULT_VERBOSE_RESPONSE = False


def get_healthchecks_config() -> HealthChecksConfig:
    """
    Get health checks configuration from Django settings or use defaults.

    Returns:
        HealthChecksConfig with readiness, startup, and liveness check paths,
        and verbose_response flag
    """
    return {
        "readiness_checks": getattr(
            settings, "HEALTHCHECKS_READINESS_CHECKS", DEFAULT_READINESS_CHECKS
        ),
        "startup_checks": getattr(
            settings, "HEALTHCHECKS_STARTUP_CHECKS", DEFAULT_STARTUP_CHECKS
        ),
        "liveness_checks": getattr(
            settings, "HEALTHCHECKS_LIVENESS_CHECKS", DEFAULT_LIVENESS_CHECKS
        ),
        "verbose_response": getattr(
            settings, "HEALTHCHECKS_VERBOSE_RESPONSE", DEFAULT_VERBOSE_RESPONSE
        ),
    }
