import dataclasses
from collections import defaultdict
from typing import List

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import Http404, HttpResponseRedirect, StreamingHttpResponse
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import FormView, TemplateView

from glom import glom
from view_breadcrumbs import BaseBreadcrumbMixin
from zgw_consumers.api_models.constants import RolOmschrijving

from open_inwoner.openzaak.api_models import Zaak
from open_inwoner.openzaak.cases import (
    connect_case_with_document,
    fetch_case_information_objects,
    fetch_case_information_objects_for_case_and_info,
    fetch_case_roles,
    fetch_single_result,
    fetch_status_history,
)
from open_inwoner.openzaak.catalog import fetch_single_status_type
from open_inwoner.openzaak.documents import (
    download_document,
    fetch_single_information_object_url,
    fetch_single_information_object_uuid,
    upload_document,
)
from open_inwoner.openzaak.models import (
    OpenZaakConfig,
    ZaakTypeConfig,
    ZaakTypeInformatieObjectTypeConfig,
)
from open_inwoner.openzaak.utils import (
    format_zaak_identificatie,
    get_role_name_display,
    is_info_object_visible,
)
from open_inwoner.utils.views import CommonPageMixin, LogMixin

from .mixins import CaseAccessMixin, OuterCaseAccessMixin, CaseLogMixin
from ..forms import CaseUploadForm


@dataclasses.dataclass
class SimpleFile:
    name: str
    size: int
    url: str


class OuterCaseDetailView(
    OuterCaseAccessMixin, CommonPageMixin, BaseBreadcrumbMixin, TemplateView
):
    template_name = "pages/cases/status_outer.html"

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn aanvragen"), reverse("cases:open_cases")),
            (
                _("Status"),
                reverse("cases:case_detail", kwargs=self.kwargs),
            ),
        ]

    def get_anchors(self):
        anchors = [["#title", _("Gegevens")]]
        anchors.append(["#statuses", _("Status")])
        anchors.append(["#documents", _("Documenten")])
        return anchors

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["hxget"] = reverse("cases:case_detail_content", kwargs=self.kwargs)
        context["anchors"] = self.get_anchors()
        return context


class InnerCaseDetailView(
    CaseLogMixin, CommonPageMixin, BaseBreadcrumbMixin, CaseAccessMixin, FormView
):
    template_name = "pages/cases/status_inner.html"
    form_class = CaseUploadForm

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn aanvragen"), reverse("cases:open_cases")),
            (
                _("Status"),
                reverse("cases:case_detail", kwargs=self.kwargs),
            ),
        ]

    def page_title(self):
        if self.case:
            return _("Status van {case}").format(case=self.case.omschrijving)
        else:
            return _("Status")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.case:
            self.log_case_access(self.case.identificatie)
            config = OpenZaakConfig.get_solo()

            documents = self.get_case_document_files(self.case)

            statuses = fetch_status_history(self.case.url)

            # NOTE we cannot sort on the Status.datum_status_gezet (datetime) because eSuite returns zeros as the time component of the datetime,
            # so we're going with the observation that on both OpenZaak and eSuite the returned list is ordered 'oldest-last'
            # here we want it 'oldest-first' so we reverse() it instead of sort()-ing
            statuses.reverse()

            status_types = defaultdict(list)
            for status in statuses:
                status_types[status.statustype].append(status)
                if self.case.status == status.url:
                    self.case.status = status

            for status_type_url, _statuses in list(status_types.items()):
                # todo parallel
                status_type = fetch_single_status_type(status_type_url)
                status_types[status_type_url] = status_type
                for status in _statuses:
                    status.statustype = status_type

            context["case"] = {
                "identification": format_zaak_identificatie(
                    self.case.identificatie, config
                ),
                "initiator": self.get_initiator_display(self.case),
                "result": self.get_result_display(self.case),
                "start_date": self.case.startdatum,
                "end_date": getattr(self.case, "einddatum", None),
                "end_date_planned": getattr(self.case, "einddatum_gepland", None),
                "end_date_legal": getattr(
                    self.case, "uiterlijke_einddatum_afdoening", None
                ),
                "description": self.case.zaaktype.omschrijving,
                "current_status": glom(
                    self.case,
                    "status.statustype.omschrijving",
                    default=_("No data available"),
                ),
                "statuses": statuses,
                "documents": documents,
                "allowed_file_extensions": sorted(config.allowed_file_extensions),
            }
            context["case"].update(self.get_upload_info_context(self.case))
            context["anchors"] = self.get_anchors(statuses, documents)
            context["hxpost"] = reverse("cases:case_detail_content", kwargs=self.kwargs)
        else:
            context["case"] = None
        return context

    def get_upload_info_context(self, case: Zaak):
        if not case:
            return {}

        internal_upload_enabled = (
            ZaakTypeInformatieObjectTypeConfig.objects.filter_enabled_for_case_type(
                case.zaaktype
            ).exists()
        )

        case_type_config_description = ""
        external_upload_enabled = False
        external_upload_url = ""

        try:
            ztc = ZaakTypeConfig.objects.filter_case_type(case.zaaktype).get()
        except ObjectDoesNotExist:
            pass
        else:
            case_type_config_description = ztc.description
            if ztc.document_upload_enabled and ztc.external_document_upload_url != "":
                external_upload_url = ztc.external_document_upload_url
                external_upload_enabled = True

        return {
            "case_type_config_description": case_type_config_description,
            "internal_upload_enabled": internal_upload_enabled,
            "external_upload_enabled": external_upload_enabled,
            "external_upload_url": external_upload_url,
        }

    def get_result_display(self, case: Zaak) -> str:
        if case.resultaat:
            result = fetch_single_result(case.resultaat)
            if result:
                return result.toelichting
        return None

    def get_initiator_display(self, case: Zaak) -> str:
        roles = fetch_case_roles(case.url, RolOmschrijving.initiator)
        if not roles:
            return ""
        return ", ".join([get_role_name_display(r) for r in roles])

    def get_case_document_files(self, case: Zaak) -> List[SimpleFile]:
        case_info_objects = fetch_case_information_objects(case.url)

        # get the information objects for the case objects

        # TODO we'd like to use parallel() but it is borked in tests
        # with parallel() as executor:
        #     info_objects = executor.map(
        #         fetch_single_information_object,
        #         [case_info.informatieobject for case_info in case_info_objects],
        #     )
        info_objects = [
            fetch_single_information_object_url(case_info.informatieobject)
            for case_info in case_info_objects
        ]

        config = OpenZaakConfig.get_solo()
        documents = []
        for case_info_obj, info_obj in zip(case_info_objects, info_objects):
            if not info_obj:
                continue
            if not is_info_object_visible(
                info_obj, config.document_max_confidentiality
            ):
                continue
            # restructure into something understood by the FileList template tag
            documents.append(
                SimpleFile(
                    name=info_obj.titel,
                    size=info_obj.bestandsomvang,
                    url=reverse(
                        "cases:document_download",
                        kwargs={
                            "object_id": case.uuid,
                            "info_id": info_obj.uuid,
                        },
                    ),
                )
            )
        return documents

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["case"] = self.case
        return kwargs

    def handle_document_upload(self, request, form):
        cleaned_data = form.cleaned_data

        file = cleaned_data["file"]
        title = cleaned_data["title"]
        document_type = cleaned_data["type"]
        source_organization = self.case.bronorganisatie

        created_document = upload_document(
            request.user,
            file,
            title,
            document_type.informatieobjecttype_url,
            source_organization,
        )
        if created_document:
            created_relationship = connect_case_with_document(
                self.case.url, created_document["url"]
            )
            if created_relationship:
                self.log_user_action(
                    request.user,
                    _("Document was uploaded for {case}: {filename}").format(
                        case=self.case.identificatie,
                        filename=file.name,
                    ),
                )
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    _("{filename} has been successfully uploaded").format(
                        filename=file.name
                    ),
                )
                return HttpResponseRedirect(self.get_success_url())

        # fail uploading the document or connecting it to the zaak
        messages.add_message(
            request,
            messages.ERROR,
            _("An error occured while uploading file {filename}").format(
                filename=file.name
            ),
        )
        return self.form_invalid(form)

    def get_success_url(self) -> str:
        return self.request.get_full_path()

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if form.is_valid():
            return self.handle_document_upload(request, form)
        else:
            return self.form_invalid(form)

    def get_anchors(self, statuses, documents):
        anchors = [["#title", _("Gegevens")]]

        if statuses:
            anchors.append(["#statuses", _("Status")])

        if documents:
            anchors.append(["#documents", _("Documenten")])

        return anchors


class CaseDocumentDownloadView(LogMixin, CaseAccessMixin, View):
    def get(self, request, *args, **kwargs):
        if not self.case:
            raise Http404

        info_object_uuid = kwargs["info_id"]
        info_object = fetch_single_information_object_uuid(info_object_uuid)
        if not info_object:
            raise Http404

        # check if this info_object belongs to this case
        if not fetch_case_information_objects_for_case_and_info(
            self.case.url, info_object.url
        ):
            raise PermissionDenied()

        # check if this info_object should be visible
        config = OpenZaakConfig.get_solo()
        if not is_info_object_visible(info_object, config.document_max_confidentiality):
            raise PermissionDenied()

        # retrieve and stream content
        content_stream = download_document(info_object.inhoud)
        if not content_stream:
            raise Http404

        self.log_user_action(
            self.request.user,
            _("Document van zaak gedownload {case}: {filename}").format(
                case=self.case.identificatie,
                filename=info_object.bestandsnaam,
            ),
        )

        headers = {
            "Content-Disposition": f'attachment; filename="{info_object.bestandsnaam}"',
            "Content-Type": info_object.formaat,
            "Content-Length": info_object.bestandsomvang,
        }
        response = StreamingHttpResponse(content_stream, headers=headers)
        return response

    def handle_no_permission(self):
        # plain error and no redirect
        raise PermissionDenied()
