from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import ClassVar, TypeVar

from django import forms
from django.contrib.admin.options import InlineModelAdmin
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from maykin_config_checks import GenericHealthCheckResult

from open_inwoner.config_checks.permissions import BasePermission
from open_inwoner.config_checks.registry import registry

TParamsForm = TypeVar("TParamsForm", bound=forms.Form)
TModel = TypeVar("TModel")


class InteractiveConfigCheck(ABC):
    identifier: ClassVar[str]
    label: ClassVar[str]
    form_class: ClassVar[type[TParamsForm]]

    @classmethod
    def get_form_kwargs(cls, obj):
        return {}

    @abstractmethod
    def run(
        self,
        form: TParamsForm,
        obj: TModel | None = None,
    ) -> GenericHealthCheckResult:
        raise NotImplementedError


def with_config_checks(
    *checks: type[InteractiveConfigCheck], target_field="config_check_links"
):
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
        setattr(admin_class, target_field, config_check_links)
        getattr(admin_class, target_field).short_description = "Interactive Checks"
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


def resolve_permissions(check_class) -> tuple[BasePermission, ...]:
    if not hasattr(check_class, "required_permissions"):
        raise ValueError(
            f"{check_class.__name__}: You must define 'required_permissions'"
        )

    permissions = check_class.required_permissions

    if not permissions:
        raise ValueError(
            f"{check_class.__name__}: You must define at least one permission class"
        )

    if not isinstance(permissions, Iterable):
        raise TypeError(
            f"{check_class.__name__}: permissions must be an iterable of BasePermission instances"
        )

    for perm in permissions:
        if not isinstance(perm, BasePermission):
            raise TypeError(
                f"{check_class.__name__}: All permission classes must inherit from BasePermission"
            )

    return tuple(permissions)
