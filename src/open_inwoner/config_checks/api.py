from typing import ClassVar, Protocol, TypeVar

from django import forms
from django.contrib.admin.options import InlineModelAdmin
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from maykin_config_checks import GenericHealthCheckResult

from open_inwoner.config_checks.registry import registry
from open_inwoner.openzaak.clients import build_zgw_client_from_service

TParamsForm = TypeVar("TParamsForm", bound=forms.Form)
TModel = TypeVar("TModel")


class InteractiveConfigCheck(Protocol[TParamsForm, TModel]):
    identifier: ClassVar[str]
    label: ClassVar[str]
    form_class: ClassVar[type[TParamsForm]]

    def __init__(self, form: TParamsForm): ...
    def run(self, obj: TModel | None) -> GenericHealthCheckResult:
        bsn = self.form.cleaned_data["bsn"]
        api_group = obj or self.form.cleaned_data["api_group"]
        if not api_group:
            raise ValueError("api_group is required")
        client = build_zgw_client_from_service(api_group.zrc_service)


def with_config_checks(*checks: InteractiveConfigCheck):
    def decorator(admin_class):
        original_init = admin_class.__init__

        def wrapped_init(self, model, admin_site):
            original_init(self, model, admin_site)

            if isinstance(self, InlineModelAdmin):
                model_to_register = self.model
            else:
                model_to_register = model
            for check in checks:
                registry.register(model_to_register, check)

        admin_class.__init__ = wrapped_init
        admin_class.config_check_links = config_check_links
        admin_class.config_check_links.short_description = "Interactive Checks"
        return admin_class

    return decorator


def config_check_links(self, obj):
    if not obj or not obj.pk:
        return "-"

    checks = registry.get_checks(type(obj))
    if not checks:
        return "-"

    app = obj._meta.app_label
    model = obj._meta.model_name

    return format_html(
        '<ul style="margin: 0; padding: 0; list-style: none; display: inline-block;">{}</ul>',
        format_html_join(
            "",
            "<li style='display: inline-block; margin-right: 5px;'><a class='button' href='{}'>{}</a></li>",
            [
                (
                    reverse(
                        "run_config_check",
                        args=[app, model, obj.pk, check.identifier],
                    ),
                    check.label,
                )
                for check in checks
            ],
        ),
    )
