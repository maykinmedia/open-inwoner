"""
Individual health check functions.

Each check function should return a CheckResult dataclass.
"""
from dataclasses import dataclass

from django.core.cache import cache
from django.db import connection


@dataclass
class CheckResult:
    """Result from a health check."""

    name: str
    success: bool
    message: str = "ok"


def check_database() -> CheckResult:
    """Check database connectivity."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return CheckResult(name="database", success=True)
    except Exception as e:
        return CheckResult(name="database", success=False, message=f"error: {str(e)}")


def check_cache() -> CheckResult:
    """Check cache connectivity."""
    try:
        cache_key = "_healthcheck_test"
        cache.set(cache_key, "test", 10)
        if cache.get(cache_key) == "test":
            cache.delete(cache_key)
            return CheckResult(name="cache", success=True)
        else:
            return CheckResult(
                name="cache", success=False, message="error: cache read failed"
            )
    except Exception as e:
        return CheckResult(name="cache", success=False, message=f"error: {str(e)}")


def check_celery() -> CheckResult:
    """Check Celery broker connectivity."""
    from celery import current_app

    try:
        # Ping workers to check broker connection and worker availability
        result = current_app.control.ping(timeout=1.0)  # type: ignore

        if not result:
            return CheckResult(
                name="celery",
                success=False,
                message="error: no workers available or broker unreachable",
            )

        return CheckResult(name="celery", success=True)
    except Exception as e:
        return CheckResult(name="celery", success=False, message=f"error: {str(e)}")
