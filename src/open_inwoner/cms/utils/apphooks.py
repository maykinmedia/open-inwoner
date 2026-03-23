import contextlib

from cms.apphook_pool import apphook_pool


class AppConfigMixin:
    """
    Replacement for aldryn_apphooks_config.mixins.AppConfigMixin.

    Sets self.namespace and self.config on the view by resolving the current
    page's apphook config. Also sets request.current_app to the namespace.
    """

    def dispatch(self, request, *args, **kwargs):
        self.namespace, self.config = get_app_instance(request)
        request.current_app = self.namespace
        return super().dispatch(request, *args, **kwargs)


def get_app_instance(request):
    """
    Get the apphook namespace and config object for the current request.

    Returns a (namespace, config) tuple. Either may be None if the current
    page is not an apphook page or has no config model.
    """
    page = getattr(request, "current_page", None)
    if not page:
        return None, None

    namespace = getattr(page, "application_namespace", None)
    app_class_name = getattr(page, "application_urls", None)
    if not namespace or not app_class_name:
        return namespace, None

    with contextlib.suppress(Exception):
        app = apphook_pool.get_apphook(app_class_name)
        if app and app.app_config:
            config = app.get_config(namespace)
            return namespace, config

    return namespace, None
