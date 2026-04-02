from django.apps import apps
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.urls import NoReverseMatch, reverse

from .registry import registry
from .signals import interactive_config_check_triggered


@staff_member_required
def run_config_check(request, app_label, model_name, pk, check_id):
    model = apps.get_model(app_label, model_name)
    obj = get_object_or_404(model, pk=pk)

    check_class = registry.get_check_by_identifier(model, check_id)
    if not check_class:
        raise Http404()

    initial = {}
    if obj:
        initial["api_group"] = obj
    form = check_class.form_class(request.POST or None, initial=initial)
    result = None

    if request.method == "POST" and form.is_valid():
        checker = check_class(form)
        selected = form.cleaned_data.get("api_group")
        target_obj = selected or obj

        result = checker.run(target_obj)

        interactive_config_check_triggered.send(
            sender=check_class,
            request=request,
            check_class=check_class,
            obj=target_obj,
            form=form,
            result=result,
        )

    opts = obj._meta
    # TODO: doublecheck this
    try:
        back_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_change", args=[obj.pk]
        )
    except NoReverseMatch:
        parent_field = next(
            (f for f in opts.get_fields() if f.one_to_many and f.concrete), None
        )
        if parent_field and hasattr(obj, parent_field.name):
            parent_obj = getattr(obj, parent_field.name)
            back_url = reverse(
                f"admin:{parent_obj._meta.app_label}_{parent_obj._meta.model_name}_change",
                args=[parent_obj.pk],
            )
        else:
            back_url = reverse("admin:index")

    return render(
        request,
        "admin/run_config_check.html",
        {
            "opts": opts,
            "back_url": back_url,
            "title": f"{check_class.label} for {obj}",
            "obj": obj,
            "original": obj,
            "form": form,
            "result": result,
        },
    )


#
# def run_config_check_standalone(request, check_id):
#     check_class = registry.get_check_by_identifier(check_id)
#
#     if not check_class:
#         raise Http404()
#
#     form = check_class.form_class(request.POST or None)
#     result = None
#     if request.method == "POST" and form.is_valid():
#         checker = check_class(form)
#         result = checker.run(None)
#
#     return render(
#         request,
#         "admin/run_config_check.html",
#         {
#             "title": f"{check_class.label}",
#             "form": form,
#             "result": result,
#         },
#     )
