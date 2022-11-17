import dataclasses
from typing import List

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.http import Http404, StreamingHttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen
from zgw_consumers.concurrent import parallel

from open_inwoner.openzaak.cases import (
    fetch_case_types,
    fetch_cases,
    fetch_single_case,
    fetch_single_case_type,
)
from open_inwoner.openzaak.info_objects import (
    InformatieObject,
    create_document_content_stream,
    fetch_case_information_objects,
    fetch_single_information_object,
    fetch_single_information_object_uuid,
)
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.statuses import (
    fetch_single_status_type,
    fetch_specific_statuses,
    fetch_status_history,
    fetch_status_types,
)


class CasesListView(
    BaseBreadcrumbMixin, LoginRequiredMixin, UserPassesTestMixin, TemplateView
):
    template_name = "pages/cases/list.html"

    @cached_property
    def crumbs(self):
        return [(_("Mijn aanvragen"), reverse("accounts:my_cases"))]

    def test_func(self):
        return self.request.user.bsn is not None

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect(reverse("root"))

        return super().handle_no_permission()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cases = fetch_cases(self.request.user.bsn)
        case_types = cache.get("case_types")
        if not case_types:
            case_types = {case_type.url: case_type for case_type in fetch_case_types()}
            cache.set("case_types", case_types, 60 * 60)
        status_types = {
            status_type.url: status_type for status_type in fetch_status_types()
        }
        current_statuses = {
            status.zaak: status
            for status in fetch_specific_statuses([case.status for case in cases])
        }
        updated_cases = []
        for case in cases:
            current_status = current_statuses[case.url]

            # If the status type does not exist in the status types, retrieve it manually
            if current_status and not current_status.statustype in status_types:
                status_type = fetch_single_status_type(current_status.statustype)
                status_types.update({status_type.url: status_type})

            updated_cases.append(
                {
                    "uuid": str(case.uuid),
                    "start_date": case.startdatum,
                    "end_date": case.einddatum if hasattr(case, "einddatum") else None,
                    "description": case.omschrijving,
                    "zaaktype_description": case_types[case.zaaktype].omschrijving
                    if case_types
                    else _("No data available"),
                    "current_status": status_types[
                        current_status.statustype
                    ].omschrijving
                    if current_status and status_types
                    else _("No data available"),
                }
            )

        context["anchors"] = [
            ("#pending_apps", _("Lopende aanvragen")),
            ("#completed_apps", _("Afgeronde aanvragen")),
        ]

        context["open_cases"] = [
            case
            for case in updated_cases
            if not case["end_date"] and not case["current_status"] == "Afgerond"
        ]
        context["open_cases"].sort(key=lambda case: case["start_date"])
        context["closed_cases"] = [
            case
            for case in updated_cases
            if case["end_date"] or case["current_status"] == "Afgerond"
        ]
        context["closed_cases"].sort(key=lambda case: case["end_date"])

        return context


@dataclasses.dataclass
class SimpleFile:
    name: str
    size: int
    url: str


def filter_info_object_visibility(
    document: InformatieObject, max_confidentiality_level: str
) -> bool:
    if not document:
        return False
    if document.status != "definitief":
        return False

    levels = [c[0] for c in VertrouwelijkheidsAanduidingen.choices]
    max_index = levels.index(max_confidentiality_level)
    doc_index = levels.index(document.vertrouwelijkheidaanduiding)

    return doc_index <= max_index


class CasesStatusView(
    BaseBreadcrumbMixin, LoginRequiredMixin, UserPassesTestMixin, TemplateView
):
    template_name = "pages/cases/status.html"

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn aanvragen"), reverse("accounts:my_cases")),
            (
                _("Status"),
                reverse("accounts:case_status", kwargs=self.kwargs),
            ),
        ]

    def test_func(self):
        return self.request.user.bsn is not None

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect(reverse("root"))

        return super().handle_no_permission()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        case_uuid = context["object_id"]
        case = fetch_single_case(case_uuid)

        if case:
            documents = self.get_case_document_files(case)

            statuses = fetch_status_history(case.url)
            statuses.sort(key=lambda status: status.datum_status_gezet)

            case_type = fetch_single_case_type(case.zaaktype)
            status_types = fetch_status_types(case_type=case.zaaktype)

            status_types_mapping = {st.url: st for st in status_types}
            for status in statuses:
                status_type = status_types_mapping[status.statustype]
                status.statustype = status_type

            context["case"] = {
                "identification": case.identificatie,
                "start_date": case.startdatum,
                "end_date": (case.einddatum if hasattr(case, "einddatum") else None),
                "description": case.omschrijving,
                "type_description": (
                    case_type.omschrijving if case_type else _("No data available")
                ),
                "current_status": (
                    statuses[-1].statustype.omschrijving
                    if statuses
                    and statuses[-1].statustype.omschrijving
                    in [st.omschrijving for st in status_types]
                    else _("No data available")
                ),
                "statuses": statuses,
                "documents": documents,
            }
            context["anchors"] = self.get_anchors(statuses, documents)
        else:
            context["case"] = None
        return context

    def get_case_document_files(self, case) -> List[SimpleFile]:
        case_info_objects = fetch_case_information_objects(case.url)

        # get the information objects for the case objects

        # TODO we'd like to use parallel() but it is borked in tests
        # with parallel() as executor:
        #     info_objects = executor.map(
        #         fetch_single_information_object,
        #         [case_info.informatieobject for case_info in case_info_objects],
        #     )
        info_objects = [
            fetch_single_information_object(case_info.informatieobject)
            for case_info in case_info_objects
        ]

        config = OpenZaakConfig.get_solo()
        documents = []
        for case_info_obj, info_obj in zip(case_info_objects, info_objects):
            if not info_obj:
                continue
            if not filter_info_object_visibility(
                info_obj, config.document_max_confidentiality
            ):
                continue
            # restructure into something understood by the FileList template tag
            documents.append(
                SimpleFile(
                    name=info_obj.bestandsnaam,
                    size=info_obj.bestandsomvang,
                    url=reverse(
                        "accounts:case_document_download",
                        kwargs={
                            "object_id": info_obj.uuid,
                        },
                    ),
                )
            )
        return documents

    def get_anchors(self, statuses, documents):
        anchors = [["#title", _("Gegevens")]]

        if statuses:
            anchors.append(["#statuses", _("Status")])

        if documents:
            anchors.append(["#documents", _("Documenten")])

        return anchors


class CasesDocumentDownloadView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.bsn is not None

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect(reverse("root"))

        return super().handle_no_permission()

    def get(self, *args, **kwargs):
        info_object_uuid = kwargs["object_id"]

        info_object = fetch_single_information_object_uuid(info_object_uuid)
        if not info_object:
            raise Http404

        config = OpenZaakConfig.get_solo()
        if not filter_info_object_visibility(
            info_object, config.document_max_confidentiality
        ):
            raise PermissionDenied()

        content_stream = create_document_content_stream(info_object.inhoud)
        if not content_stream:
            raise Http404

        headers = {
            "Content-Disposition": f'attachment; filename="{info_object.bestandsnaam}"',
            "Content-Type": info_object.formaat,
            "Content-Length": info_object.bestandsomvang,
        }
        response = StreamingHttpResponse(content_stream, headers=headers)
        return response
