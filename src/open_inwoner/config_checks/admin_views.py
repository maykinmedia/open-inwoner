from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from open_inwoner.openzaak.models import ZGWApiGroupConfig

from .fetch_cases import FetchCasesConfigCheck
from .forms import FetchCasesConfigCheckParams


@staff_member_required
def run_fetch_cases_check(request, api_group_id):
    api_group = ZGWApiGroupConfig.objects.get(pk=api_group_id)

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
        "admin/run_fetch_cases_check.html",
        {
            "form": form,
            "result": result,
            "api_group": api_group,
        },
    )
