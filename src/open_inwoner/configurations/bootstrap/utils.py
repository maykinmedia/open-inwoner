import logging

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
