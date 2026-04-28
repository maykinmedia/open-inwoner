from django.dispatch import receiver

from open_inwoner.config_checks.signals import interactive_config_check_post_run
from open_inwoner.utils.logentry import user_action


@receiver(interactive_config_check_post_run)
def log_interactive_check(sender, request, check_class, obj, result, **kwargs):
    if obj is None:
        return
    status = "success" if result.success else "failure"

    user_action(
        request,
        obj,
        f"Configuration check '{check_class.identifier}' executed "
        f"for object '{obj}' with result: {status}",
    )
