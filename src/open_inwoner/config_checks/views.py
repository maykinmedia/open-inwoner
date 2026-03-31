from django.apps import apps
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from .registry import registry


@staff_member_required
def run_config_check(request, app_label, model_name, pk, check_id):
    model = apps.get_model(app_label, model_name)
    obj = get_object_or_404(model, pk=pk)

    checks = registry.get_checks(model)

    check_class = next(
        (c for c in checks if c.identifier == check_id),
        None,
    )

    if not check_class:
        raise Http404()

    form = check_class.form_class(request.POST or None)
    result = None

    if request.method == "POST" and form.is_valid():
        checker = check_class(form)
        result = checker.run(obj)
    display_name = str(obj)
    return render(
        request,
        "admin/run_config_check.html",
        {
            "opts": obj._meta,
            "title": f"{check_class.label} for {display_name}",
            "obj": obj,
            "original": obj,
            "form": form,
            "result": result,
        },
    )
