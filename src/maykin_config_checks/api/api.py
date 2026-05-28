from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.utils.html import format_html

from maykin_config_checks.registry import registry


def with_config_checks(*checks, url_name="run_config_check"):
    def decorator(admin_class):
        if any(type(v) is admin_class for v in admin.site._registry.values()):
            raise ImproperlyConfigured(
                f"@with_config_checks on {admin_class.__name__} must be applied as the "
                "inner decorator (i.e. closer to the class). Place @admin.register above "
                "@with_config_checks, otherwise the admin is instantiated before "
                "__init__ is wrapped and checks are never registered with the model."
            )

        original_init = admin_class.__init__

        def wrapped_init(self, model, admin_site):
            original_init(self, model, admin_site)

            self.config_check_url_name = url_name

            target_model = getattr(self, "model", model)

            for check in checks:
                registry.register(check, model=target_model)

        admin_class.__init__ = wrapped_init
        admin_class.config_check_links = config_check_links
        return admin_class

    return decorator


def config_check_links(self, obj):
    if not obj or not obj.pk:
        return "-"

    checks = registry.get_checks(type(obj))

    if not checks:
        return "-"

    links = []

    for check in checks:
        url = reverse(
            self.config_check_url_name,
            args=[
                obj._meta.app_label,
                obj._meta.model_name,
                obj.pk,
                check.identifier,
            ],
        )
        links.append(f'<a class="button" href="{url}">{check.label}</a>')

    return format_html(" ".join(links))
