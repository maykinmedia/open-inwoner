from datetime import datetime
from typing import Union

from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.generic.edit import FormView

from .client import JaaropgaveClient, UitkeringClient
from .forms import MonthlyReportsForm, YearlyReportsForm


class BenefitsFormView(LoginRequiredMixin, FormView):
    template_name: str
    form_class: forms.Form
    ssd_client: Union[JaaropgaveClient, UitkeringClient]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        client = self.ssd_client()

        context["client"] = client

        if "report" in self.request.GET:
            dt = datetime.strptime(self.request.GET["report"], "%Y-%m-%d")
            context["report_date"] = dt

        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()

        if form.is_valid():
            client = self.get_context_data()["client"]

            bsn = request.user.bsn
            report_date_iso = form.data["report_date"]
            base_url = request.build_absolute_uri()

            pdf_content = client.get_report(bsn, report_date_iso, base_url)

            if pdf_content is None:
                return redirect(
                    self.request.get_full_path() + f"?report={report_date_iso}"
                )

            pdf_name = client.format_file_name(report_date_iso)

            response = HttpResponse(pdf_content, content_type="application/pdf")
            response["Content-Disposition"] = f"attachment; filename={pdf_name}.pdf"
            return response


class MonthlyBenefitsFormView(BenefitsFormView):
    template_name = "pages/ssd/monthly_reports_list.html"
    form_class = MonthlyReportsForm
    ssd_client = UitkeringClient


class YearlyBenefitsFormView(BenefitsFormView):
    template_name = "pages/ssd/yearly_reports_list.html"
    form_class = YearlyReportsForm
    ssd_client = JaaropgaveClient
