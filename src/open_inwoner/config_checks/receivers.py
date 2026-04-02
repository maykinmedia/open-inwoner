from django.dispatch import receiver

import structlog

from .signals import interactive_config_check_triggered

logger = structlog.get_logger(__name__)


@receiver(interactive_config_check_triggered)
def log_interactive_check(sender, request, check_class, obj, result, **kwargs):
    user = request.user
    status = "success" if result.success else "failure"

    logger.info(
        "interactive_config_check_run",
        user=str(user),
        check_id=check_class.identifier,
        target_object=str(obj),
        status=status,
    )
