import dataclasses
from typing import List, Optional

from django.contrib.auth.mixins import AccessMixin
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

from open_inwoner.openzaak.api_models import Zaak
from open_inwoner.openzaak.cases import (
    fetch_case_information_objects,
    fetch_case_information_objects_for_case_and_info,
    fetch_cases,
    fetch_roles_for_case_and_bsn,
    fetch_single_case,
    fetch_specific_status,
    fetch_status_history,
)
from open_inwoner.openzaak.catalog import (
    fetch_single_case_type,
    fetch_single_status_type,
    fetch_status_types,
)
from open_inwoner.openzaak.documents import (
    download_document,
    fetch_single_information_object,
)
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.utils import is_info_object_visible, is_zaak_visible


class CaseAccessMixin(AccessMixin):
    """
    Shared authorisation check

    Base checks:
    - user is authenticated
    - user has a BSN

    When retrieving a case :
    - users BSN has a role for this case
    """

    case: Zaak = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if not request.user.bsn:
            return self.handle_no_permission()

        self.case = self.get_case(kwargs)
        if self.case:
            # check if we have a role in this case
            if not fetch_roles_for_case_and_bsn(self.case.url, request.user.bsn):
                return self.handle_no_permission()

            # check confidentiality level
            if not is_zaak_visible(self.case):
                return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect(reverse("root"))

        return super().handle_no_permission()

    def get_case(self, kwargs) -> Optional[Zaak]:
        case_uuid = kwargs.get("object_id")
        if not case_uuid:
            return None

        return fetch_single_case(case_uuid)


class CaseListView(BaseBreadcrumbMixin, CaseAccessMixin, TemplateView):
    template_name = "pages/cases/list.html"

    @cached_property
    def crumbs(self):
        return [(_("Mijn aanvragen"), reverse("accounts:my_cases"))]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cases = fetch_cases(self.request.user.bsn)

        case_types = {}
        status_types = {}
        temp_status_types = []
        current_statuses = {}

        for case in cases:
            # Fetch new case types
            if case.zaaktype not in case_types.keys():
                case_type = fetch_single_case_type(case.zaaktype)
                case_types.update({case_type.url: case_type})

            # Fetch list of case's status types and each one (unique) separately
            temp_status_types += [st.url for st in fetch_status_types(case.zaaktype)]

            for status_type_url in set(temp_status_types):
                if status_type_url not in status_types:
                    status_type = fetch_single_status_type(status_type_url)
                    status_types.update({status_type.url: status_type})

            # Fetch case's current status
            current_status = fetch_specific_status(case.status)
            current_statuses.update({current_status.zaak: current_status})

        # Prepare data for frontend
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


class CaseDetailView(BaseBreadcrumbMixin, CaseAccessMixin, TemplateView):
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.case:
            documents = self.get_case_document_files(self.case)

            statuses = fetch_status_history(self.case.url)
            statuses.sort(key=lambda status: status.datum_status_gezet)

            case_type = fetch_single_case_type(self.case.zaaktype)
            status_types = fetch_status_types(case_type=self.case.zaaktype)

            status_types_mapping = {st.url: st for st in status_types}
            for status in statuses:
                status_type = status_types_mapping[status.statustype]
                status.statustype = status_type

            context["case"] = {
                "identification": self.case.identificatie,
                "start_date": self.case.startdatum,
                "end_date": (
                    self.case.einddatum if hasattr(self.case, "einddatum") else None
                ),
                "description": self.case.omschrijving,
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
            fetch_single_information_object(url=case_info.informatieobject)
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
                    name=info_obj.bestandsnaam,
                    size=info_obj.bestandsomvang,
                    url=reverse(
                        "accounts:case_document_download",
                        kwargs={
                            "object_id": case.uuid,
                            "info_id": info_obj.uuid,
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


class CaseDocumentDownloadView(CaseAccessMixin, View):
    def get(self, request, *args, **kwargs):
        if not self.case:
            raise Http404

        info_object_uuid = kwargs["info_id"]
        info_object = fetch_single_information_object(uuid=info_object_uuid)
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
