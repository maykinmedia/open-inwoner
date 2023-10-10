from datetime import datetime

from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.generic.edit import FormView

from furl import furl

from .client import JaaropgaveClient, UitkeringClient
from .forms import MonthlyReportsForm, YearlyReportsForm


class BenefitsFormView(LoginRequiredMixin, FormView):
    template_name: str
    form_class: forms.Form

    def post(self, request, *args, **kwargs):
        form = self.get_form()

        if form.is_valid():
            ssd_client = self.get_context_data()["client"]

            bsn = request.user.bsn
            report_date = ssd_client.format_report_date(form.data["report_date"])
            request_base_url = request.build_absolute_uri()

            pdf_content = ssd_client.get_reports(bsn, report_date, request_base_url)

            if not pdf_content:
                return_path = request.get_full_path()
                return_path_furled = furl(return_path).add(
                    {"report": f"{report_date}", "status": "not_found"}
                )
                return redirect(return_path_furled.url)

            pdf_name = ssd_client.format_file_name(report_date)
            response = HttpResponse(pdf_content, content_type="application/pdf")
            response["Content-Disposition"] = f"attachment; filename={pdf_name}.pdf"
            return response


class MonthlyBenefitsFormView(BenefitsFormView):
    template_name = "pages/ssd/monthly_reports_list.html"
    form_class = MonthlyReportsForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["client"] = UitkeringClient()

        if "status" in self.request.GET:
            context["report_not_found"] = datetime.strptime(
                self.request.GET["report"], "%Y%m"
            )

        return context


class YearlyBenefitsFormView(BenefitsFormView):
    template_name = "pages/ssd/yearly_reports_list.html"
    form_class = YearlyReportsForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["client"] = JaaropgaveClient()

        if "status" in self.request.GET:
            context["report_not_found"] = datetime.strptime(
                self.request.GET["report"], "%Y"
            )

        return context
