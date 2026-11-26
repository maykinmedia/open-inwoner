from typing import Any

from django.http import HttpRequest, HttpResponseBase

import structlog
from aldryn_apphooks_config.app_base import CMSConfigApp
from aldryn_apphooks_config.mixins import AppConfigMixin
from aldryn_apphooks_config.models import AppHookConfig
from aldryn_apphooks_config.utils import get_app_instance
from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from cms.models import Page

logger = structlog.stdlib.get_logger(__name__)


class ApphookConfigMixin(AppConfigMixin):
    """
    `AppConfigMixin` that logs a warning when no apphook config is found.

    aldryn resolves the config by looking up the URL namespace of the page, and
    quietly sets `self.config` to `None` if no config has that namespace. Each view
    then falls back to its own default (hiding sections, allowing pages, default
    headings), so a page/config namespace mismatch looks like a feature that is
    simply not showing up. Django CMS's page settings form masks the mismatch too,
    by displaying the first config in its dropdown as if it were selected.

    The config is resolved in `setup()` rather than `dispatch()`, so subclasses can
    use `self.config` in their own `dispatch()` before calling `super()`.
    """

    namespace: str
    config: AppHookConfig | None

    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        super().setup(request, *args, **kwargs)
        self.namespace, self.config = get_app_instance(request)
        request.current_app = self.namespace

        if self.config is None:
            self._log_config_not_found(request)

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        # Skip `AppConfigMixin.dispatch`, which would resolve the config again
        return super(AppConfigMixin, self).dispatch(request, *args, **kwargs)

    def _log_config_not_found(self, request: HttpRequest) -> None:
        # Only queried on this error path: the namespaces that do exist are what
        # tell an admin which side (page or config) to fix
        page: Page | None = getattr(request, "current_page", None)
        apphook: str | None = page.application_urls if page else None
        app: CMSApp | None = apphook_pool.get_apphook(apphook) if apphook else None
        available_namespaces: list[str] = (
            list(app.get_configs().values_list("namespace", flat=True))
            if isinstance(app, CMSConfigApp)
            else []
        )

        logger.warning(
            "apphook_config_not_found",
            namespace=self.namespace,
            path=request.path,
            page_id=page.pk if page else None,
            apphook=apphook,
            available_namespaces=available_namespaces,
        )
