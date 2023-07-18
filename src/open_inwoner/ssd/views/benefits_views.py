from typing import Union

from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView
from django.views.generic.edit import FormView

from ..client import JaaropgaveClient, UitkeringClient
from ..forms import MonthlyReportsForm, YearlyReportsForm
from ..utils import strip_extension


#
# Benefits reports form views
#
class BenefitsFormView(LoginRequiredMixin, FormView):
    template_name: str
    form_class: forms.Form
    success_url: str
    success_reverse: str

    def get_success_url(self):
        form = self.get_form()

        return reverse_lazy(
            self.success_reverse,
            kwargs={
                "file_name": form.data["report"],
            },
        )


class MonthlyBenefitsFormView(BenefitsFormView):
    template_name = "pages/ssd/monthly_reports_list.html"
    form_class = MonthlyReportsForm
    success_reverse = "profile:download_monthly_benefits"


class YearlyBenefitsFormView(BenefitsFormView):
    template_name = "pages/ssd/yearly_reports_list.html"
    form_class = YearlyReportsForm
    success_reverse = "profile:download_yearly_benefits"


#
# Download views
#
class DownloadBenefitsView(LoginRequiredMixin, DetailView):
    """Base class for the download views"""

    ssd_client: Union[JaaropgaveClient, UitkeringClient]
    fail_reverse: str

    def get(self, request, *args, **kwargs):
        file_name = strip_extension(kwargs["file_name"])
        bsn = request.user.bsn

        pdf_file = self.ssd_client.get_report(bsn, file_name)

        # no report found: redirect back to index view
        if pdf_file is None:
            return redirect(reverse(self.fail_reverse) + f"?report={file_name}")

        response = HttpResponse(pdf_file, content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename={file_name}.pdf"
        return response


class DownloadYearlyBenefitsView(DownloadBenefitsView):
    ssd_client = JaaropgaveClient()
    fail_reverse = "profile:yearly_benefits_index"


class DownloadMonthlyBenefitsView(DownloadBenefitsView):
    ssd_client = UitkeringClient()
    fail_reverse = "profile:monthly_benefits_index"
