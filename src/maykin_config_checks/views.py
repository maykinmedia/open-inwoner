from typing import Any

from django.apps import apps
from django.db.models import Model
from django.forms import Form
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseForbidden, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import NoReverseMatch, reverse

from maykin_config_checks.registry import registry


def run_config_check(
    request: HttpRequest,
    check_id: str,
    app_label: str | None = None,
    model_name: str | None = None,
    pk: int | None = None,
) -> HttpResponse:
    # Enforce base-line access: authenticated users with staff priviliges
    if not request.user.is_authenticated or not request.user.is_staff:
        raise PermissionDenied

    obj: Model | None = None
    model: type[Model] | None = None

    if app_label and model_name:
        model = apps.get_model(app_label, model_name)

        if model is None:
            raise Http404(f"Model {app_label}_{model_name} not found")

        if pk is not None:
            obj = get_object_or_404(model, pk=pk)

    check_class = registry.get_check(check_id)

    if check_class is None:
        raise Http404(f"No check registered with id={check_id}")

    form_class = getattr(check_class, "form_class", None)

    if form_class is None:
        raise ValueError(f"{check_class.__name__} must define 'form_class'")

    permissions = getattr(check_class, "required_permissions", None)

    if permissions is None:
        raise ValueError(f"{check_class.__name__} must define 'required_permissions'")

    failed = [
        perm.get_error_message(obj)
        for perm in permissions
        if not perm.has_permission(request, obj)
    ]

    if failed:
        return HttpResponseForbidden("\n".join(failed))

    form_kwargs: dict[str, Any] = check_class.get_form_kwargs(instance=obj)

    form: Form = form_class(
        request.POST if request.method == "POST" else None,
        **form_kwargs,
    )
    result = None

    if request.method == "POST" and form.is_valid():
        checker = check_class()
        result = checker.run(
            form.cleaned_data,
            instance=obj,
            request=request,
        )

    if obj:
        try:
            back_url = reverse(
                f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change",
                args=[obj.pk],
            )
        except NoReverseMatch:
            back_url = reverse("admin:index")
    else:
        back_url = reverse("admin:index")

    return render(
        request,
        "admin/run_config_check.html",
        {
            "title": check_class.label,
            "opts": model._meta if model else None,
            "original": obj,
            "obj": obj,
            "form": form,
            "result": result,
            "back_url": back_url,
        },
    )
