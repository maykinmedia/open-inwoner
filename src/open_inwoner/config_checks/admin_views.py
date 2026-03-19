from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from open_inwoner.openzaak.models import ZGWApiGroupConfig

from .fetch_brp import FetchBRPConfigCheck
from .fetch_cases import FetchCasesConfigCheck
from .fetch_userfeed import FetchUserfeedConfigCheck
from .forms import (
    FetchBRPConfigCheckParams,
    FetchCasesConfigCheckParams,
    FetchUserfeedConfigCheckParams,
)


@staff_member_required
def run_fetch_cases_check(request, api_group_id):
    api_group = get_object_or_404(ZGWApiGroupConfig, pk=api_group_id)

    result = None

    if request.method == "POST":
        form = FetchCasesConfigCheckParams(request.POST)

        if form.is_valid():
            api_group = form.cleaned_data["api_group"]
            bsn = form.cleaned_data["bsn"]

            check = FetchCasesConfigCheck(api_group, bsn)
            result = check()

    else:
        form = FetchCasesConfigCheckParams(initial={"api_group": api_group})

    return render(
        request,
        "admin/run_config_check.html",
        {
            "form": form,
            "result": result,
            "title": f"Fetch cases check for {api_group.name}",
            "back_url": reverse("admin:openzaak_openzaakconfig_changelist"),
        },
    )


@staff_member_required
def run_fetch_brp_check(request):
    result = None

    if request.method == "POST":
        form = FetchBRPConfigCheckParams(request.POST)

        if form.is_valid():
            bsn = form.cleaned_data["bsn"]

            check = FetchBRPConfigCheck(bsn)
            result = check()
    else:
        form = FetchBRPConfigCheckParams()

    return render(
        request,
        "admin/run_config_check.html",
        {
            "form": form,
            "result": result,
            "title": "Fetch BRP check",
            "back_url": reverse("admin:haalcentraal_haalcentraalconfig_change"),
        },
    )


@staff_member_required
def run_fetch_userfeed_check(request):
    result = None

    initial = {}
    if request.GET.get("user"):
        initial["user"] = request.GET["user"]

    if request.method == "POST":
        form = FetchUserfeedConfigCheckParams(request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            check = FetchUserfeedConfigCheck(user)
            result = check()
    else:
        form = FetchUserfeedConfigCheckParams(initial=initial)

    return render(
        request,
        "admin/run_config_check.html",
        {
            "form": form,
            "result": result,
            "title": "Fetch userfeed check",
            "back_url": reverse("admin:accounts_user_changelist"),
        },
    )
