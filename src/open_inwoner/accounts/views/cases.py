import dataclasses
from collections import defaultdict
from typing import List, Optional

from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import Http404, HttpResponseRedirect, StreamingHttpResponse
from django.shortcuts import redirect
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
    fetch_cases,
    fetch_roles_for_case_and_bsn,
    fetch_single_case,
    fetch_single_result,
    fetch_single_status,
    fetch_status_history,
)
from open_inwoner.openzaak.catalog import (
    fetch_single_case_type,
    fetch_single_status_type,
)
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
    is_zaak_visible,
)
from open_inwoner.utils.mixins import PaginationMixin
from open_inwoner.utils.views import CommonPageMixin, LogMixin

from ...openzaak.formapi import fetch_open_submissions
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
            return redirect("/")

        return super().handle_no_permission()

    def get_case(self, kwargs) -> Optional[Zaak]:
        case_uuid = kwargs.get("object_id")
        if not case_uuid:
            return None

        return fetch_single_case(case_uuid)


class CaseListMixin(CaseLogMixin, PaginationMixin):
    paginate_by = 9

    def get_cases(self) -> List[Zaak]:
        cases = fetch_cases(self.request.user.bsn)

        case_types = {}
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

        # fetch case status resources and attach resolved to case
        status_types = defaultdict(list)
        for case in cases:
            if case.status:
                # todo parallel
                case.status = fetch_single_status(case.status)
                status_types[case.status.statustype].append(case)

        for status_type_url, _cases in status_types.items():
            # todo parallel
            status_type = fetch_single_status_type(status_type_url)
            for case in _cases:
                case.status.statustype = status_type

        return cases

    def process_cases(self, cases: List[Zaak]) -> List[dict]:
        # Prepare data for frontend
        config = OpenZaakConfig.get_solo()

        updated_cases = []
        for case in cases:
            case_dict = {
                "identificatie": format_zaak_identificatie(case.identificatie, config),
                "uuid": str(case.uuid),
                "start_date": case.startdatum,
                "end_date": getattr(case, "einddatum", None),
                "description": case.zaaktype.omschrijving,
                "current_status": glom(
                    case, "status.statustype.omschrijving", default=""
                ),
            }
            updated_cases.append(case_dict)
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
        return context

    def get_anchors(self) -> list:
        return []


class InnerOpenCaseListView(
    CommonPageMixin, CaseAccessMixin, CaseListMixin, TemplateView
):
    template_name = "pages/cases/inner_list.html"

    def page_title(self):
        return _("Lopende aanvragen")

    def get_cases(self):
        all_cases = super().get_cases()

        cases = [case for case in all_cases if not case.einddatum]
        cases.sort(key=lambda case: case.startdatum, reverse=True)
        return cases

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["hxget"] = "cases:open_cases_content"
        return context


class OuterOpenCaseListView(CommonPageMixin, BaseBreadcrumbMixin, TemplateView):
    template_name = "pages/cases/outer_list.html"

    @cached_property
    def crumbs(self):
        return [(_("Mijn aanvragen"), reverse("cases:open_cases"))]

    def page_title(self):
        return _("Lopende aanvragen")

    def get_anchors(self) -> list:
        return [
            (reverse("cases:open_submissions"), _("Open aanvragen")),
            ("#cases", _("Lopende aanvragen")),
            (reverse("cases:closed_cases"), _("Afgeronde aanvragen")),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["anchors"] = self.get_anchors()
        context["hxget"] = "cases:open_cases_content"
        return context


class InnerClosedCaseListView(
    CommonPageMixin, CaseAccessMixin, CaseListMixin, TemplateView
):
    template_name = "pages/cases/inner_list.html"

    def page_title(self):
        return _("Afgeronde aanvragen")

    def get_cases(self):
        all_cases = super().get_cases()

        cases = [case for case in all_cases if case.einddatum]
        cases.sort(key=lambda case: case.einddatum, reverse=True)
        return cases

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["hxget"] = "cases:closed_cases_content"
        return context


class OuterClosedCaseListView(CommonPageMixin, BaseBreadcrumbMixin, TemplateView):
    template_name = "pages/cases/outer_list.html"

    @cached_property
    def crumbs(self):
        return [(_("Mijn aanvragen"), reverse("cases:closed_cases"))]

    def page_title(self):
        return _("Afgeronde aanvragen")

    def get_anchors(self) -> list:
        return [
            (reverse("cases:open_submissions"), _("Open aanvragen")),
            (reverse("cases:open_cases"), _("Lopende aanvragen")),
            ("#cases", _("Afgeronde aanvragen")),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["anchors"] = self.get_anchors()
        context["hxget"] = "cases:closed_cases_content"
        return context


class OpenSubmissionListView(
    CommonPageMixin, BaseBreadcrumbMixin, CaseAccessMixin, TemplateView
):
    template_name = "pages/cases/submissions.html"

    @cached_property
    def crumbs(self):
        return [(_("Mijn aanvragen"), reverse("cases:open_submissions"))]

    def page_title(self):
        return _("Open aanvragen")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["submissions"] = self.get_submissions()
        context["anchors"] = self.get_anchors()
        return context

    def get_submissions(self):
        submissions = fetch_open_submissions(self.request.user.bsn)
        return submissions

    def get_anchors(self) -> list:
        return [
            ("#submissions", _("Open aanvragen")),
            (reverse("cases:open_cases"), _("Lopende aanvragen")),
            (reverse("cases:closed_cases"), _("Afgeronde aanvragen")),
        ]


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
