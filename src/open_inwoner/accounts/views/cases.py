import dataclasses
from typing import List, Optional

from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect, StreamingHttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import FormView, TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin
from zgw_consumers.api_models.constants import RolOmschrijving

from open_inwoner.openzaak.api_models import Zaak
from open_inwoner.openzaak.cases import (
    fetch_case_information_objects,
    fetch_case_information_objects_for_case_and_info,
    fetch_case_roles,
    fetch_cases,
    fetch_roles_for_case_and_bsn,
    fetch_single_case,
    fetch_single_result,
    fetch_specific_status,
    fetch_status_history,
)
from open_inwoner.openzaak.catalog import fetch_single_case_type, fetch_status_types
from open_inwoner.openzaak.documents import (
    download_document,
    fetch_single_information_object_url,
    fetch_single_information_object_uuid,
)
from open_inwoner.openzaak.models import (
    OpenZaakConfig,
    ZaakTypeInformatieObjectTypeConfig,
)
from open_inwoner.openzaak.utils import (
    get_role_name_display,
    is_info_object_visible,
    is_zaak_visible,
)
from open_inwoner.utils.mixins import PaginationMixin
from open_inwoner.utils.views import CommonPageMixin, LogMixin

from ..forms import CaseUploadForm


class CaseLogMixin(LogMixin):
    def log_case_access(self, case_identificatie: str):
        self.log_user_action(
            self.request.user,
            _("Zaak bekeken: {case}").format(case=case_identificatie),
        )


class CaseAccessMixin(AccessMixin):
    """
    Shared authorisation check

    Base checks:
    - user is authenticated
    - user has a BSN

    When retrieving a case :
    - users BSN has a role for this case
    - case confidentiality is not higher than globally configured
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

            # resolve case-type
            self.case.zaaktype = fetch_single_case_type(self.case.zaaktype)
            if not self.case.zaaktype:
                return self.handle_no_permission()

            # check if case + case-type are visible
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


class CaseListMixin(CaseLogMixin, PaginationMixin):
    paginate_by = 9
    template_name = "pages/cases/list.html"

    def get_cases(self) -> List[Zaak]:
        cases = fetch_cases(self.request.user.bsn)

        case_types = {}
        status_types = {}
        case_types_set = {case.zaaktype for case in cases}

        # fetch unique case types
        for case_type_url in case_types_set:
            # todo parallel
            case_types[case_type_url] = fetch_single_case_type(case_type_url)

        # set resolved case types
        for case in cases:
            case.zaaktype = case_types[case.zaaktype]

        # filter visibility
        cases = [case for case in cases if is_zaak_visible(case)]

        # grab types of remaining cases
        case_types_set = {case.zaaktype.url for case in cases}

        # fetch status types for case types
        for case_type_url in case_types_set:
            # todo parallel
            for st in fetch_status_types(case_type_url):
                status_types[st.url] = st

        # fetch case status resources and attach resolved to case
        for case in cases:
            # todo parallel
            if case.status:
                case.status = fetch_specific_status(case.status)
                case.status.statustype = status_types[case.status.statustype]

        return cases

    def process_cases(self, cases: List[Zaak]) -> List[Zaak]:
        # Prepare data for frontend
        updated_cases = []
        for case in cases:
            updated_cases.append(
                {
                    "identificatie": str(case.identificatie),
                    "uuid": str(case.uuid),
                    "start_date": case.startdatum,
                    "end_date": getattr(case, "einddatum", None),
                    "description": case.omschrijving,
                    "zaaktype_description": case.zaaktype.omschrijving,
                    "current_status": case.status.statustype.omschrijving
                    if case.status
                    else "",
                }
            )
        return updated_cases

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        raw_cases = self.get_cases()
        paginator_dict = self.paginate_with_context(raw_cases)
        cases = self.process_cases(paginator_dict["object_list"])

        context["cases"] = cases
        context.update(paginator_dict)

        for case in cases:
            self.log_case_access(case["identificatie"])

        context["anchors"] = self.get_anchors()
        context["title"] = self.get_title()
        return context

    def get_anchors(self) -> list:
        return []

    def get_title(self) -> str:
        return ""


class OpenCaseListView(
    CommonPageMixin, BaseBreadcrumbMixin, CaseAccessMixin, CaseListMixin, TemplateView
):
    @cached_property
    def crumbs(self):
        return [(_("Mijn aanvragen"), reverse("accounts:my_open_cases"))]

    def page_title(self):
        return _("Lopende aanvragen")

    def get_cases(self):
        all_cases = super().get_cases()

        cases = [case for case in all_cases if not case.einddatum]
        cases.sort(key=lambda case: case.startdatum, reverse=True)
        return cases

    def get_anchors(self) -> list:
        return [
            ("#cases", _("Lopende aanvragen")),
            (reverse("accounts:my_closed_cases"), _("Afgeronde aanvragen")),
        ]

    def get_title(self) -> str:
        return _("Lopende aanvragen")


class ClosedCaseListView(
    CommonPageMixin, BaseBreadcrumbMixin, CaseAccessMixin, CaseListMixin, TemplateView
):
    @cached_property
    def crumbs(self):
        return [(_("Mijn aanvragen"), reverse("accounts:my_closed_cases"))]

    def page_title(self):
        return _("Afgeronde aanvragen")

    def get_cases(self):
        all_cases = super().get_cases()

        cases = [case for case in all_cases if case.einddatum]
        cases.sort(key=lambda case: case.einddatum, reverse=True)
        return cases

    def get_anchors(self) -> list:
        return [
            (reverse("accounts:my_open_cases"), _("Lopende aanvragen")),
            ("#cases", _("Afgeronde aanvragen")),
        ]

    def get_title(self) -> str:
        return _("Afgeronde aanvragen")


@dataclasses.dataclass
class SimpleFile:
    name: str
    size: int
    url: str


class CaseDetailView(
    CaseLogMixin, CommonPageMixin, BaseBreadcrumbMixin, CaseAccessMixin, FormView
):
    template_name = "pages/cases/status.html"
    form_class = CaseUploadForm

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn aanvragen"), reverse("accounts:my_open_cases")),
            (
                _("Status"),
                reverse("accounts:case_status", kwargs=self.kwargs),
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

            documents = self.get_case_document_files(self.case)

            statuses = fetch_status_history(self.case.url)
            # NOTE we cannot sort on the Status.datum_status_gezet (datetime) because eSuite returns zeros as the time component of the datetime,
            # so we're going with the observation that on both OpenZaak and eSuite the returned list is ordered 'oldest-last'
            # here we want it 'oldest-first' so we reverse() it instead of sort()-ing
            statuses.reverse()

            status_types = fetch_status_types(self.case.zaaktype.url)

            status_types_mapping = {st.url: st for st in status_types}
            for status in statuses:
                status_type = status_types_mapping[status.statustype]
                status.statustype = status_type

            context["case"] = {
                "identification": self.case.identificatie,
                "initiator": self.get_initiator_display(self.case),
                "result": self.get_result_display(self.case),
                "start_date": self.case.startdatum,
                "end_date": getattr(self.case, "einddatum", None),
                "end_date_planned": getattr(self.case, "einddatum_gepland", None),
                "end_date_legal": getattr(
                    self.case, "uiterlijke_einddatum_afdoening", None
                ),
                "description": self.case.omschrijving,
                "type_description": self.case.zaaktype.omschrijving,
                "current_status": (
                    statuses[-1].statustype.omschrijving
                    if statuses
                    and statuses[-1].statustype.omschrijving
                    in [st.omschrijving for st in status_types]
                    else _("No data available")
                ),
                "statuses": statuses,
                "documents": documents,
                "upload_enabled": (
                    True
                    if ZaakTypeInformatieObjectTypeConfig.objects.case_type_iotc_visible(
                        self.case
                    )
                    else False
                ),
            }
            context["anchors"] = self.get_anchors(statuses, documents)
        else:
            context["case"] = None
        return context

    def get_result_display(self, case) -> str:
        if case.resultaat:
            result = fetch_single_result(case.resultaat)
            if result:
                return result.toelichting
        return _("Onbekend")

    def get_initiator_display(self, case) -> str:
        roles = fetch_case_roles(case.url, RolOmschrijving.initiator)
        if not roles:
            return ""
        return ", ".join([get_role_name_display(r) for r in roles])

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

    def get_case_type_information_type_object_config_ids(self) -> List[str]:
        if not self.case:
            return []

        case_type_iotc_visible = (
            ZaakTypeInformatieObjectTypeConfig.objects.case_type_iotc_visible(self.case)
        )
        return [_type.id for _type in case_type_iotc_visible]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        case_type_iotc_ids = self.get_case_type_information_type_object_config_ids()

        document_choices = []
        for index, id in enumerate(case_type_iotc_ids):
            document_choices.append(
                (
                    index,
                    ZaakTypeInformatieObjectTypeConfig.objects.get(id=id).omschrijving,
                )
            )
        kwargs["document_choices"] = document_choices
        return kwargs

    def get_success_url(self) -> str:
        return self.request.get_full_path()

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        file = request.FILES["file"]

        if form.is_valid():
            messages.add_message(
                self.request,
                messages.SUCCESS,
                _(f"{file.name} has been successfully uploaded."),
            )
            return HttpResponseRedirect(self.get_success_url())
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
