import logging

from zgw_consumers.models import Service

RED = "\033[31m"
NORMAL = "\033[0m"

logger = logging.getLogger(__name__)


def convert_setting_to_model_field_name(setting: str, namespace: str) -> str:
    return setting.split(f"{namespace}_", 1)[1].lower()


def log_form_errors(config_step, form):
    logger.error(
        "%s"
        % f"\n\n{RED}There are problems with the settings for {config_step.verbose_name}:{NORMAL}"
    )
    for field, errors in form.errors.items():
        logger.error("%s : %s" % (field, "; ".join(errors)))


def get_service(slug: str) -> Service:
    """
    Try to find a Service and re-raise DoesNotExist with the identifier to make debugging
    easier
    """
    try:
        return Service.objects.get(slug=slug)
    except Service.DoesNotExist as e:
        raise Service.DoesNotExist(f"{str(e)} (identifier = {slug})")
