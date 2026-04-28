from datetime import datetime

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views.generic.base import RedirectView
from django.views.generic.edit import FormView

import structlog
from furl import furl
from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.utils.views import CommonPageMixin

from .client import JaaropgaveClient, UitkeringClient
from .exceptions import SSDClientException, SSDServiceFaultException
from .forms import MonthlyReportsForm, YearlyReportsForm

logger = structlog.stdlib.get_logger(__name__)


class MonthlyBenefitsIndexView(RedirectView):
    permanent = False
    query_string = True
    pattern_name = "ssd:monthly_benefits_index"


class BenefitsFormView(
    LoginRequiredMixin, BaseBreadcrumbMixin, CommonPageMixin, FormView
):
    template_name: str
    form_class: forms.Form

    @cached_property
    def crumbs(self):
        current_page = self.request.current_page
        title = current_page.get_title() if current_page else ("Mijn uitkeringen")
        return [
            (title, reverse("ssd:uitkeringen")),
        ]

    def post(self, request, *args, **kwargs):
        form = self.get_form()

        if form.is_valid():
            ssd_client = self.get_context_data()["client"]

            bsn = request.user.bsn
            report_date = ssd_client.format_report_date(form.data["report_date"])
            request_url = request.build_absolute_uri()

            try:
                pdf_content = ssd_client.get_reports(bsn, report_date, request_url)
            except (ImproperlyConfigured, SSDServiceFaultException) as exc:
                logger.warning(
                    "SSD service fault",
                    meldingen=[m.tekst for m in exc.meldingen],
                )
                messages.error(
                    request=request,
                    message=_(
                        "Your report(s) could not be retrieved due to technical problems. "
                        "Please contact the municipality."
                    ),
                )
                pdf_content = None
            except SSDClientException:
                logger.exception("SSD client error")
                messages.error(
                    request=request,
                    message=_(
                        "Your report(s) could not be retrieved due to technical problems. "
                        "Please try again later."
                    ),
                )
                pdf_content = None

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
