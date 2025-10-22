import structlog
from zgw_consumers.models import Service

logger = structlog.stdlib.get_logger(__name__)


def convert_setting_to_model_field_name(setting: str, namespace: str) -> str:
    return setting.split(f"{namespace}_", 1)[1].lower()


def log_form_errors(config_step, form):
    logger.error(
        "Bootstrap configuration problems",
        configuration_step=config_step.verbose_name,
    )
    for field, errors in form.errors.items():
        logger.error(
            "Bootstrap validation error", field=field, errors="; ".join(errors)
        )


def get_service(slug: str) -> Service:
    """
    Try to find a Service and re-raise DoesNotExist with the identifier to make debugging
    easier
    """
    try:
        return Service.objects.get(slug=slug)
    except Service.DoesNotExist as exc:
        raise Service.DoesNotExist(f"{str(exc)} (identifier = {slug})") from exc
