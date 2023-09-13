from datetime import datetime
from typing import Type, Union

from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic.edit import FormView

from .client import JaaropgaveClient, UitkeringClient
from .forms import MonthlyReportsForm, YearlyReportsForm


class BenefitsFormView(LoginRequiredMixin, FormView):
    template_name: str
    form_class: forms.Form
    ssd_client_type: Union[Type[JaaropgaveClient], Type[UitkeringClient]]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        client = self.ssd_client_type()

        context["client"] = client

        if "not_found" in self.request.GET:
            dt = datetime.strptime(self.request.GET["report"], "%Y-%m-%d")
            context["date_report_not_found"] = dt

        return context

    def post(self, request, *args, **kwargs):
        if "multiple_reports" in request.session:
            del request.session["multiple_reports"]

        form = self.get_form()

        if form.is_valid():
            client = self.get_context_data()["client"]

            bsn = request.user.bsn
            report_date_iso = form.data["report_date"]
            request_base_url = request.build_absolute_uri()

            pdf_contents = client.get_reports(bsn, report_date_iso, request_base_url)
            # pdf_content = client.get_reports(bsn, report_date_iso, request_base_url)

            # no content
            if pdf_contents is None:
                return redirect(
                    self.request.get_full_path()
                    + f"?report={report_date_iso}&not_found"
                )
            # single report (default)
            elif len(pdf_contents) == 1:
                pdf_name = client.format_file_name(report_date_iso)

                response = HttpResponse(pdf_contents[0], content_type="application/pdf")
                response["Content-Disposition"] = f"attachment; filename={pdf_name}.pdf"
                return response
            # multiple reports (vakantiegeld)
            else:
                import zipfile
                from io import BytesIO
                from zipfile import ZipFile

                archive = BytesIO()
                with ZipFile(archive, "w") as zip_obj:
                    for index, pdf in enumerate(pdf_contents):
                        pdf_name = (
                            f"{client.format_file_name(report_date_iso)} ({index})"
                        )
                        zip_obj.writestr(pdf_name, pdf)

                response = HttpResponse(
                    archive.getvalue(), content_type="application/zip"
                )
                response["Content-Disposition"] = "attachment; filename=uitkeringen.zip"
                return response


class MonthlyBenefitsFormView(BenefitsFormView):
    template_name = "pages/ssd/monthly_reports_list.html"
    form_class = MonthlyReportsForm
    ssd_client_type = UitkeringClient


class YearlyBenefitsFormView(BenefitsFormView):
    template_name = "pages/ssd/yearly_reports_list.html"
    form_class = YearlyReportsForm
    ssd_client_type = JaaropgaveClient
