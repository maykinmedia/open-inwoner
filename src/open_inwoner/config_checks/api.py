from django.urls import reverse
from django.utils.html import format_html

from .registry import registry


def with_config_checks(*checks):
    def decorator(admin_class):
        original_init = admin_class.__init__

        def wrapped_init(self, model, admin_site):
            original_init(self, model, admin_site)

            for check in checks:
                registry.register(model, check)

        admin_class.__init__ = wrapped_init
        admin_class.config_check_links = config_check_links
        return admin_class

    return decorator


def config_check_links(self, obj):
    if not obj:
        return "-"

    checks = registry.get_checks(type(obj))

    links = []

    for check in checks:
        url = reverse(
            "run_config_check",
            args=[
                obj._meta.app_label,
                obj._meta.model_name,
                obj.pk,
                check.identifier,
            ],
        )
        links.append(f'<a class="button" href="{url}">{check.label}</a>')

    return format_html(" ".join(links))
