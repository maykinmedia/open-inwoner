from django.apps import apps
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.urls import NoReverseMatch, reverse

from .api import resolve_permissions
from .registry import registry
from .signals import interactive_config_check_post_run, interactive_config_check_pre_run


def run_config_check(request, app_label, model_name, check_id, pk=None):
    model = apps.get_model(app_label, model_name)

    obj = None
    if pk is not None:
        obj = get_object_or_404(model, pk=pk)

    check_class = registry.get_check_by_identifier(model, check_id)
    if not check_class:
        raise Http404()

    permissions = resolve_permissions(check_class)

    failed_reasons = []

    for perm in permissions:
        if not perm.has_permission(request):
            failed_reasons.append(perm.get_error_message(None))
            continue

        if obj is not None and not perm.has_object_permission(request, obj):
            failed_reasons.append(perm.get_error_message(obj))

    opts = model._meta

    if obj:
        try:
            back_url = reverse(
                f"admin:{opts.app_label}_{opts.model_name}_change",
                args=[obj.pk],
            )
        except NoReverseMatch:
            back_url = reverse("admin:index")
    else:
        back_url = reverse("admin:index")

    if failed_reasons:
        return render(
            request,
            "admin/permission_denied.html",
            {
                "opts": opts,
                "obj": obj,
                "title": "Permission Denied",
                "failed_reasons": failed_reasons,
                "back_url": back_url,
            },
            status=403,
        )

    form_kwargs = getattr(check_class, "get_form_kwargs", lambda obj: {})(obj)
    form = check_class.form_class(request.POST or None, **form_kwargs)

    result = None

    if request.method == "POST" and form.is_valid():
        checker = check_class()
        target_obj = getattr(
            checker,
            "get_target_object",
            lambda form, obj: obj,
        )(form, obj)

        interactive_config_check_pre_run.send(
            sender=check_class,
            request=request,
            check_class=check_class,
            obj=target_obj,
            form=form,
        )

        result = checker.run(form, target_obj)

        interactive_config_check_post_run.send(
            sender=check_class,
            request=request,
            check_class=check_class,
            obj=target_obj,
            form=form,
            result=result,
        )

    title = check_class.label if not obj else f"{check_class.label} for {obj}"

    return render(
        request,
        "admin/run_config_check.html",
        {
            "opts": opts,
            "back_url": back_url,
            "title": title,
            "obj": obj,
            "original": obj,
            "form": form,
            "result": result,
        },
    )
