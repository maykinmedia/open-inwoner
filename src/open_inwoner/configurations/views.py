from django.http import HttpRequest
from django.shortcuts import redirect
from django.views.decorators.http import require_safe

import structlog

from open_inwoner.configurations.models import SiteConfiguration

logger = structlog.stdlib.get_logger(__name__)


@require_safe
def redirect_to_configured_security_txt(request: HttpRequest):
    config = SiteConfiguration.get_solo()
    logger.debug(
        "Redirecting to configured security text",
        request_path=request.path,
        target=config.security_txt_redirect_target,
    )
    return redirect(config.security_txt_redirect_target, permanent=False)
