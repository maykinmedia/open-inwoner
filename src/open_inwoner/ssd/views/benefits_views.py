from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views.generic import DetailView, TemplateView

from ..client import JaaropgaveClient, UitkeringClient
from ..utils import strip_extension


class MonthlyBenefitsListView(LoginRequiredMixin, TemplateView):
    template_name = "pages/ssd/monthly_reports_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # TODO: make this configurable in admin
        monthly_benefits = ["May 2023", "June 2023"]
        context["monthly_benefits"] = monthly_benefits

        return context


class YearlyBenefitsListView(LoginRequiredMixin, TemplateView):
    template_name = "pages/ssd/yearly_reports_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # TODO: make this configurable in admin
        yearly_benefits = ["2022", "2023"]
        context["yearly_benefits"] = yearly_benefits

        return context


class DownloadBenefitsView(LoginRequiredMixin, DetailView):
    """Base class for the download views"""


class DownloadYearlyBenefitsView(DownloadBenefitsView):
    """Download yearly benefits reports ('Jaaropgaven')"""

    ssd_client = JaaropgaveClient()

    def get(self, request, *args, **kwargs):
        file_name = kwargs["file_name"]
        file_name = strip_extension(file_name)

        bsn = request.user.bsn

        pdf_file = self.ssd_client.get_yearly_report(bsn, file_name)

        response = HttpResponse(pdf_file, content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename={file_name}.pdf"
        return response


class DownloadMonthlyBenefitsView(DownloadBenefitsView):
    """Download monthly benefits reports ('Maandspecificaties')"""

    ssd_client = UitkeringClient()

    def get(self, request, *args, **kwargs):
        file_name = kwargs["file_name"]
        file_name_stem = strip_extension(file_name)

        bsn = request.user.bsn
        period = self.ssd_client.file_name_to_period(file_name)

        pdf_file = self.ssd_client.get_monthly_report(bsn, period)

        response = HttpResponse(pdf_file, content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename={file_name_stem}.pdf"
        return response
