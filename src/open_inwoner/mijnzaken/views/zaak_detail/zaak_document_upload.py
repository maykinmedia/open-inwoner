import logging

from django.contrib import messages
from django.http import Http404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from django_htmx.http import HttpResponseClientRedirect

from open_inwoner.openzaak.models import ZGWApiGroupConfig
from open_inwoner.utils.views import LogMixin

from ...forms import CaseUploadForm
from ..mixins import CaseAccessMixin

logger = logging.getLogger(__name__)


class CaseDocumentUploadFormView(CaseAccessMixin, LogMixin, FormView):
    template_name = "pages/cases/document_form.html"
    form_class = CaseUploadForm

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if form.is_valid() and not getattr(self.case, "einddatum", None):
            return self.handle_document_upload(request, form)
        return self.form_invalid(form)

    def handle_document_error(self, request, file):
        messages.add_message(
            request,
            messages.ERROR,
            _("An error occured while uploading file {filename}").format(
                filename=file.name
            ),
        )

        return HttpResponseClientRedirect(
            reverse(
                "cases:case_detail",
                kwargs={
                    "object_id": str(self.case.uuid),
                    "api_group_id": self.kwargs["api_group_id"],
                },
            )
        )

    def handle_document_upload(self, request, form):
        try:
            api_group = ZGWApiGroupConfig.objects.get(pk=self.kwargs["api_group_id"])
        except ZGWApiGroupConfig.DoesNotExist as exc:
            logger.exception("Non-existent ZGWApiGroupConfig passed")
            raise Http404 from exc

        cleaned_data = form.cleaned_data
        files = cleaned_data["files"]

        created_documents = []

        for file in files:
            title = file.name
            document_type = cleaned_data["type"]
            source_organization = self.case.bronorganisatie

            created_document = api_group.documenten_client.upload_document(
                request.user,
                file,
                title,
                document_type.informatieobjecttype_url,
                source_organization,
            )
            if not created_document:
                return self.handle_document_error(request, file)

            created_relationship = api_group.zaken_client.connect_case_with_document(
                self.case.url, created_document.get("url")
            )
            if not created_relationship:
                return self.handle_document_error(request, file)

            self.log_user_action(
                request.user,
                _("Document was uploaded for {case}: {filename}").format(
                    case=self.case.identificatie,
                    filename=file.name,
                ),
            )
            created_documents.append(created_document)

        success_message = (
            _("Wij hebben **{num_uploaded} bestand(en)** succesvol geüpload:").format(
                num_uploaded=len(created_documents)
            )
            + "\n\n"
            + "\n".join(f"- {doc['titel']}" for doc in created_documents)
        )
        messages.add_message(
            request,
            messages.SUCCESS,
            success_message,
            extra_tags="as_markdown local_message",
        )

        self.request.session["uploads"] = True

        return HttpResponseClientRedirect(
            reverse(
                "cases:case_detail",
                kwargs={
                    "object_id": str(self.case.uuid),
                    "api_group_id": self.kwargs["api_group_id"],
                },
            )
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["case"] = self.case
        return kwargs

    def get_success_url(self):
        return reverse(
            "cases:case_detail_document_form",
            kwargs={
                "object_id": str(self.case.uuid),
                "api_group_id": self.kwargs["api_group_id"],
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["hxpost_document_action"] = reverse(
            "cases:case_detail_document_form", kwargs=self.kwargs
        )
        return context
