from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views.generic import DetailView, TemplateView

from ..utils import generate_pdf, get_filename_stem


class BenefitsOverview(LoginRequiredMixin, TemplateView):
    template_name = "pages/ssd/benefits_overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # TODO: retrieve benefits reports via SSD client
        # hard-coded for now
        yearly_benefits = ["example.html", "example.txt"]
        monthly_benefits = ["example.txt", "file.jpg"]

        context["yearly_benefits"] = yearly_benefits
        context["monthly_benefits"] = monthly_benefits

        return context


class DownloadBenefitsView(LoginRequiredMixin, DetailView):
    def get(self, request, *args, **kwargs):
        file_name = kwargs["file_name"]
        file_name_stem = get_filename_stem(file_name)

        # TODO: refactor file_url construction based on how benefits are retrieved
        file_url = settings.SENDFILE_ROOT + "/" + file_name

        # TODO: generation of PDFs should be moved to SSD client
        pdf_file = generate_pdf(file_url)

        response = HttpResponse(pdf_file, content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename={file_name_stem}.pdf"
        return response


class DownloadYearlyBenefitsView(DownloadBenefitsView):
    """Download yearly benefits reports ('Jaaropgaven')"""


class DownloadMonthlyBenefitsView(DownloadBenefitsView):
    """Download monthly benefits reports ('Maandspecificaties')"""
