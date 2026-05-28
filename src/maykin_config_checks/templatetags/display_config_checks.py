from collections.abc import Iterable

from django import template

from .. import ConfigCheckResult

register = template.Library()


@register.inclusion_tag("configuration_config_check.html")
def display_config_checks(
    check_results: Iterable[ConfigCheckResult],
) -> dict[str, Iterable[ConfigCheckResult]]:
    """Display the verbose name and the message of each (failed) result."""
    successful_checks = []
    failed_checks = []
    for check_result in check_results:
        if check_result.success:
            successful_checks.append(check_result)
        else:
            failed_checks.append(check_result)

    return {
        "successful_checks": successful_checks,
        "failed_checks": failed_checks,
    }
