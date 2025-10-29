from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.utils.module_loading import import_string
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe

from .checks import CheckResult
from .config import get_healthchecks_config


@method_decorator(never_cache, name="dispatch")
@method_decorator(require_safe, name="dispatch")
class BaseHealthCheckView(View):
    """
    Base view for health check endpoints.

    Subclasses should specify which config key to use for checks.
    """

    config_key: str  # Should be set in subclass

    def get_check_paths(self) -> list[str]:
        """Get the list of check paths from configuration."""
        config = get_healthchecks_config()
        return config[self.config_key]  # type: ignore

    def run_checks(self, check_paths: list[str]) -> tuple[dict[str, str], bool]:
        """
        Run a list of health checks by importing and executing them.

        Args:
            check_paths: List of dotted paths to check functions

        Returns:
            Tuple of (checks_dict, all_healthy_bool)
        """
        checks = {}
        all_healthy = True

        for check_path in check_paths:
            try:
                check_func = import_string(check_path)
                result: CheckResult = check_func()
                checks[result.name] = result.message
                if not result.success:
                    all_healthy = False
            except Exception as e:
                # If the check function itself fails to import or run
                check_name = check_path.split(".")[-1]
                checks[check_name] = f"error: {str(e)}"
                all_healthy = False

        return checks, all_healthy

    def get(self, request: HttpRequest) -> HttpResponse:
        """Execute health checks and return appropriate response."""
        check_paths = self.get_check_paths()

        if not check_paths:
            # No checks configured, just return OK
            return HttpResponse("OK")

        checks, all_healthy = self.run_checks(check_paths)
        status_code = 200 if all_healthy else 503

        config = get_healthchecks_config()
        verbose = config["verbose_response"]

        # Allow ?format=json to override for verbose responses
        if request.GET.get("format") == "json" and verbose:
            return JsonResponse(
                {
                    "status": self.get_status_label(all_healthy),
                    "checks": checks,
                },
                status=status_code,
            )

        if all_healthy:
            return HttpResponse("OK", status=status_code)
        else:
            if verbose:
                return HttpResponse(
                    self.get_verbose_error_message(checks), status=status_code
                )
            else:
                return HttpResponse("NOT OK", status=status_code)

    def get_status_label(self, all_healthy: bool) -> str:
        """Get the status label for JSON responses. Can be overridden."""
        return "healthy" if all_healthy else "unhealthy"

    def get_verbose_error_message(self, checks: dict[str, str]) -> str:
        """Get verbose error message. Can be overridden."""
        return f"Service Unavailable: {', '.join(f'{k}={v}' for k, v in checks.items())}"


@never_cache
@require_safe
def health(request: HttpRequest) -> HttpResponse:
    """
    Basic health check endpoint.
    Returns a simple 200 OK response to indicate the application is running.
    Common endpoints: /health, /health/, /healthz
    """
    return HttpResponse("OK")


class LivenessView(BaseHealthCheckView):
    """
    Liveness probe endpoint (Kubernetes-style).
    Indicates whether the application is alive and running.
    Can be configured with checks via HEALTHCHECKS_LIVENESS_CHECKS setting.
    Common endpoints: /liveness, /live, /livez
    """

    config_key = "liveness_checks"


class ReadinessView(BaseHealthCheckView):
    """
    Readiness probe endpoint (Kubernetes-style).
    Checks if the application is ready to accept traffic.
    Checks are configured via HEALTHCHECKS_READINESS_CHECKS setting.
    Common endpoints: /readiness, /ready, /readyz
    """

    config_key = "readiness_checks"


class StartupView(BaseHealthCheckView):
    """
    Startup probe endpoint (Kubernetes-style).
    Indicates whether the application has finished starting up.
    Checks are configured via HEALTHCHECKS_STARTUP_CHECKS setting.
    Common endpoints: /startup, /startupz
    """

    config_key = "startup_checks"

    def get_status_label(self, all_healthy: bool) -> str:
        """Override status label for startup checks."""
        return "ready" if all_healthy else "not_ready"

    def get_verbose_error_message(self, checks: dict[str, str]) -> str:
        """Override verbose error message for startup checks."""
        return "Service Starting"


# View aliases
liveness = LivenessView.as_view()
readiness = ReadinessView.as_view()
startup = StartupView.as_view()
