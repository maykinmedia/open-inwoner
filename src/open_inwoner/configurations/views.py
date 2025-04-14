import logging

from django.http import HttpRequest
from django.shortcuts import redirect
from django.views.decorators.http import require_safe

from open_inwoner.configurations.models import SiteConfiguration

logger = logging.getLogger(__name__)


@require_safe
def redirect_to_configured_security_txt(request: HttpRequest):
    config = SiteConfiguration.get_solo()
    logger.debug(
        "Redirecting %s to %s",
        request.path,
        config.security_txt_redirect_target,
    )
    return redirect(config.security_txt_redirect_target, permanent=False)
