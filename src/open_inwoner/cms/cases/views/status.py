import dataclasses
import datetime as dt
import logging
from collections import defaultdict
from datetime import datetime
from typing import List, Optional

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import Http404, StreamingHttpResponse
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import FormView, TemplateView

from django_htmx.http import HttpResponseClientRedirect
from mail_editor.helpers import find_template
from view_breadcrumbs import BaseBreadcrumbMixin
from zgw_consumers.api_models.constants import RolOmschrijving
from zgw_consumers.concurrent import parallel

from open_inwoner.openklant.clients import build_client as build_client_openklant
from open_inwoner.openklant.models import OpenKlantConfig
from open_inwoner.openklant.wrap import get_fetch_parameters
from open_inwoner.openzaak.api_models import Status, StatusType, Zaak
from open_inwoner.openzaak.clients import (
    ZakenClient,
    build_client as build_client_openzaak,
)
from open_inwoner.openzaak.documents import (
    fetch_single_information_object_url,
    fetch_single_information_object_uuid,
)
from open_inwoner.openzaak.models import (
    OpenZaakConfig,
    StatusTranslation,
    ZaakTypeConfig,
    ZaakTypeInformatieObjectTypeConfig,
    ZaakTypeResultaatTypeConfig,
    ZaakTypeStatusTypeConfig,
)
from open_inwoner.openzaak.utils import get_role_name_display, is_info_object_visible
from open_inwoner.userfeed import hooks
from open_inwoner.utils.time import has_new_elements
from open_inwoner.utils.translate import TranslationLookup
from open_inwoner.utils.views import CommonPageMixin, LogMixin

from ..forms import CaseContactForm, CaseUploadForm
from .mixins import CaseAccessMixin, CaseLogMixin, OuterCaseAccessMixin

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class SimpleFile:
    name: str
    size: int
    url: str
    created: Optional[datetime] = None


class OuterCaseDetailView(
    OuterCaseAccessMixin, CommonPageMixin, BaseBreadcrumbMixin, TemplateView
):
    template_name = "pages/cases/status_outer.html"

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn aanvragen"), reverse("cases:index")),
            (
                _("Status"),
                reverse("cases:case_detail", kwargs=self.kwargs),
            ),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["hxget"] = reverse("cases:case_detail_content", kwargs=self.kwargs)
        context["custom_anchors"] = True
        return context


class InnerCaseDetailView(
    CaseLogMixin, CommonPageMixin, BaseBreadcrumbMixin, CaseAccessMixin, FormView
):
    template_name = "pages/cases/status_inner.html"
    form_class = CaseUploadForm
    contact_form_class = CaseContactForm
    case: Optional[Zaak] = None

    def store_statustype_mapping(self, zaaktype_identificatie):
        # Filter on ZaakType identificatie to avoid eSuite situation where one statustype
        # is linked to multiple zaaktypes
        self.statustype_config_mapping = {
            zaaktype_statustype.statustype_url: zaaktype_statustype
            for zaaktype_statustype in ZaakTypeStatusTypeConfig.objects.filter(
                zaaktype_config__identificatie=zaaktype_identificatie
            )
        }

    def store_resulttype_mapping(self, zaaktype_identificatie):
        # Filter on ZaakType identificatie to avoid eSuite situation where one resulttype
        # is linked to multiple zaaktypes
        self.resulttype_config_mapping = {
            zt_resulttype.resultaattype_url: zt_resulttype
            for zt_resulttype in ZaakTypeResultaatTypeConfig.objects.filter(
                zaaktype_config__identificatie=zaaktype_identificatie
            )
        }

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn aanvragen"), reverse("cases:index")),
            (
                _("Status"),
                reverse("cases:case_detail", kwargs=self.kwargs),
            ),
        ]

    def page_title(self):
        return _("Status")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # case is retrieved via CaseAccessMixin
        if self.case:
            self.log_access_case_detail(self.case)

            config = OpenZaakConfig.get_solo()
            status_translate = StatusTranslation.objects.get_lookup()

            zaken_client = build_client_openzaak("zaak")

            # fetch data associated with `self.case`
            documents = self.get_case_document_files(self.case, zaken_client)
            statuses = zaken_client.fetch_status_history(self.case.url)
            self.store_statustype_mapping(self.case.zaaktype.identificatie)
            self.store_resulttype_mapping(self.case.zaaktype.identificatie)

            statustypen = []
            if catalogi_client := build_client_openzaak("catalogi"):
                statustypen = catalogi_client.fetch_status_types_no_cache(
                    self.case.zaaktype.url
                )

            # NOTE we cannot sort on the Status.datum_status_gezet (datetime) because eSuite
            # returns zeros as the time component of the datetime, so we're going with the
            # observation that on both OpenZaak and eSuite the returned list is ordered 'oldest-last'
            # here we want it 'oldest-first' so we reverse() it instead of sort()-ing
            statuses.reverse()

            # get preview of second status
            if len(statuses) == 1:
                second_status_preview = self.get_second_status_preview(statustypen)
            else:
                second_status_preview = None

            # handle/transform data associated with `self.case`
            status_types_mapping = self.sync_statuses_with_status_types(
                statuses, zaken_client
            )
            end_statustype_data = self.handle_end_statustype_data(
                status_types_mapping=status_types_mapping,
                end_statustype=self.handle_end_statustype(statuses, statustypen),
                status_translate=status_translate,
            )
            result_data = self.get_result_data(
                self.case, self.resulttype_config_mapping, zaken_client
            )

            hooks.case_status_seen(self.request.user, self.case)
            hooks.case_documents_seen(self.request.user, self.case)

            context["case"] = {
                "id": str(self.case.uuid),
                "identification": self.case.identification,
                "initiator": self.get_initiator_display(self.case),
                "result": result_data.get("display", ""),
                "result_description": result_data.get("description", ""),
                "start_date": self.case.startdatum,
                "end_date": getattr(self.case, "einddatum", None),
                "end_date_planned": getattr(self.case, "einddatum_gepland", None),
                "end_date_legal": getattr(
                    self.case, "uiterlijke_einddatum_afdoening", None
                ),
                "description": self.case.zaaktype.omschrijving,
                "statuses": self.get_statuses_data(
                    statuses, status_translate, self.statustype_config_mapping
                ),
                # "end_statustype_data": end_statustype_data,
                "end_statustype_data": end_statustype_data,
                "second_status_preview": second_status_preview,
                "documents": documents,
                "allowed_file_extensions": sorted(config.allowed_file_extensions),
                "new_docs": has_new_elements(
                    documents,
                    "created",
                    dt.timedelta(days=settings.DOCUMENT_RECENT_DAYS),
                ),
            }
            context["case"].update(self.get_upload_info_context(self.case))
            context["anchors"] = self.get_anchors(statuses, documents)
            context["contact_form"] = self.contact_form_class()
            context["hxpost_contact_action"] = reverse(
                "cases:case_detail_contact_form", kwargs=self.kwargs
            )
            context["hxpost_document_action"] = reverse(
                "cases:case_detail_document_form", kwargs=self.kwargs
            )
        else:
            context["case"] = None

        return context

    def get_second_status_preview(self, statustypen: list) -> Optional[StatusType]:
        """
        Get the relevant status type to display preview of second case status

        Note: we cannot assume that the "second" statustype has the `volgnummer` 2;
              hence we get all statustype_numbers, sort in ascending order, and let
              the "second" statustype be that with `volgnummer == statustype_numbers[1]`
        """
        statustype_numbers = [s.volgnummer for s in statustypen]

        # status_types retrieved via eSuite don't always have a volgnummer
        if not all(statustype_numbers):
            return

        # only 1 statustype for `self.case`
        # (this scenario is blocked by openzaak, but not part of the zgw standard)
        if len(statustype_numbers) < 2:
            logger.info("Case {case} has only one statustype".format(case=self.case))
            return

        statustype_numbers.sort()

        return next(
            filter(
                lambda s: s.volgnummer == statustype_numbers[1] and not s.is_eindstatus,
                statustypen,
            ),
            None,
        )

    def sync_statuses_with_status_types(
        self, statuses: list[Status], zaken_client: ZakenClient
    ) -> dict[str, StatusType]:
        """
        Update `statuses` (including the status on this view) and sync with `status_types`:
            - resolve `self.case.status` (a url/str) to a `Status` object
            - resolve `status_type` url for each element in `statuses` to the corresponding
              `StatusType` object (this also mutates `self.case.status`)
            - create mapping `{status_type_url: StatusType}`

        We create a preliminary mapping {status_type url: Status}, then loop over this mapping
        replacing `Status` with the `StatusType` corresponding to the url, and resolving the
        `status_type` url on each `Status` instance to the corresponding `StatusType` object.
        Note that this works by mutating `statuses`.

        Requires eSuite compatibility check for cases where the current status of our case is
        not returned as part of the statuslist retrieval.
        """
        status_types_mapping = defaultdict(list)

        # preliminary mapping {status_type url: status}
        for status in statuses:
            status_types_mapping[status.statustype].append(status)
            if self.case.status == status.url:
                self.case.status = status

        # eSuite compatibility
        if isinstance(self.case.status, str):
            logger.info(
                "Issue #2037 -- Retrieving status individually because of eSuite"
            )
            self.case.status = zaken_client.fetch_single_status(self.case.status)
            status_types_mapping[self.case.status.statustype].append(self.case.status)
            statuses.append(self.case.status)

        catalogi_client = build_client_openzaak("catalogi")
        if catalogi_client is None:
            return status_types_mapping

        # final mapping {status_type url: status_type}
        for status_type_url, _statuses in list(status_types_mapping.items()):
            status_type = catalogi_client.fetch_single_status_type(status_type_url)
            status_types_mapping[status_type_url] = status_type
            # resolve statustype url to `StatusType`
            for status in _statuses:
                status.statustype = status_type

        return status_types_mapping

    def handle_end_statustype(
        self, statuses: list[Status], statustypen: list[StatusType]
    ):
        """
        Determine the statustype of the endstatus in `statustypen` (if there is one)

        Requires eSuite compatibility check for cases containing multiple statustypes
        per zaaktype with `isEindstatus: true`. When reaching a `statustype` with
        `isEindstatus: true`, we assume this is our end status.
        """
        # The end status data is not passed if the end status has been reached,
        # because in that case the end status data is already included in `statuses`
        end_statustype = next((s for s in statustypen if s.is_eindstatus), None)

        # eSuite compatibility
        if (
            statuses
            and statuses[-1].statustype
            and statuses[-1].statustype.is_eindstatus
        ):
            end_statustype = statuses[-1].statustype

        return end_statustype

    def handle_end_statustype_data(
        self,
        status_types_mapping: dict[str, StatusType],
        end_statustype: StatusType,
        status_translate: StatusTranslation,
    ):
        """
        Prepare data about end statustype for use in context/template
        """
        end_statustype_data = None
        if not status_types_mapping.get(end_statustype.url):
            end_statustype_data = {
                "label": status_translate(
                    end_statustype.omschrijving, default=_("No data available")
                ),
                "status_indicator": getattr(
                    self.statustype_config_mapping.get(end_statustype.url),
                    "status_indicator",
                    None,
                ),
                "status_indicator_text": getattr(
                    self.statustype_config_mapping.get(end_statustype.url),
                    "status_indicator_text",
                    None,
                ),
                "call_to_action_url": getattr(
                    self.statustype_config_mapping.get(end_statustype.url),
                    "call_to_action_url",
                    None,
                ),
                "call_to_action_text": getattr(
                    self.statustype_config_mapping.get(end_statustype.url),
                    "call_to_action_text",
                    None,
                ),
                "case_link_text": getattr(
                    self.statustype_config_mapping.get(end_statustype.url),
                    "case_link_text",
                    _("Bekijk aanvraag"),
                ),
            }
        return end_statustype_data

    @property
    def is_file_upload_enabled_for_case_type(self) -> bool:
        case_upload_enabled = (
            ZaakTypeInformatieObjectTypeConfig.objects.filter_enabled_for_case_type(
                self.case.zaaktype
            ).exists()
        )
        logger.info(
            "Case {url} has case type file upload: {case_upload_enabled}".format(
                url=self.case.url, case_upload_enabled=case_upload_enabled
            )
        )
        return case_upload_enabled

    @property
    def is_file_upload_enabled_for_statustype(self) -> bool:
        try:
            enabled_for_status_type = self.statustype_config_mapping[
                self.case.status.statustype.url
            ].document_upload_enabled
        except AttributeError as e:
            logger.exception(e)
            logger.info(
                "Could not retrieve status type for case {case}; "
                "the status has not been resolved to a ZGW model object.".format(
                    case=self.case
                )
            )
            return True
        except KeyError as e:
            logger.exception(e)
            logger.info(
                "Could not retrieve status type config for url {url}".format(
                    url=self.case.status.statustype.url
                )
            )
            return True
        logger.info(
            "Case {url} status type {status_type} has status type file upload: {enabled_for_status_type}".format(
                url=self.case.url,
                status_type=self.case.status.statustype,
                enabled_for_status_type=enabled_for_status_type,
            )
        )
        return enabled_for_status_type

    @property
    def is_internal_file_upload_enabled(self) -> bool:
        return (
            self.is_file_upload_enabled_for_case_type
            and self.is_file_upload_enabled_for_statustype
        )

    def get_upload_info_context(self, case: Zaak):
        if not case:
            return {}

        open_klant_config = OpenKlantConfig.get_solo()

        case_type_config_description = ""
        case_type_document_upload_description = ""
        external_upload_enabled = False
        external_upload_url = ""
        contact_form_enabled = False

        try:
            ztc = ZaakTypeConfig.objects.filter_case_type(case.zaaktype).get()
        except ObjectDoesNotExist:
            pass
        else:
            case_type_config_description = ztc.description
            contact_form_enabled = ztc.contact_form_enabled
            if ztc.document_upload_enabled and ztc.external_document_upload_url != "":
                external_upload_url = ztc.external_document_upload_url
                external_upload_enabled = True

            try:
                zt_statustype_config = ztc.zaaktypestatustypeconfig_set.get(
                    statustype_url=case.status.statustype.url
                )
            # case has no status, or statustype config not found
            except (AttributeError, ObjectDoesNotExist):
                pass
            else:
                case_type_document_upload_description = (
                    zt_statustype_config.document_upload_description
                )

        # disable document upload message
        if self.request.session.get("uploads", ""):
            case_type_document_upload_description = ""
            del self.request.session["uploads"]

        return {
            "case_type_config_description": case_type_config_description,
            "case_type_document_upload_description": case_type_document_upload_description,
            "internal_upload_enabled": self.is_internal_file_upload_enabled
            and not getattr(self.case, "einddatum", None),
            "external_upload_enabled": external_upload_enabled
            and not getattr(self.case, "einddatum", None),
            "external_upload_url": external_upload_url,
            "contact_form_enabled": (
                contact_form_enabled and open_klant_config.has_register()
            ),
        }

    @staticmethod
    def get_result_data(
        case: Zaak, result_type_config_mapping: dict, client: ZakenClient
    ) -> dict:
        if not case.resultaat:
            return {}

        result = client.fetch_single_result(case.resultaat)

        display = result.toelichting
        description = getattr(
            result_type_config_mapping.get(result.resultaattype), "description", ""
        )

        return {
            "display": display,
            "description": description,
        }

    @staticmethod
    def get_initiator_display(case: Zaak) -> str:
        if client := build_client_openzaak("zaak"):
            roles = client.fetch_case_roles(case.url, RolOmschrijving.initiator)
            return ", ".join([get_role_name_display(r) for r in roles])
        return ""

    @staticmethod
    def get_statuses_data(
        statuses: List[Status],
        lookup: TranslationLookup,
        statustype_config_mapping: Optional[dict] = None,
    ) -> List[dict]:
        return [
            {
                "date": s.datum_status_gezet,
                "label": lookup.from_glom(
                    s, "statustype.omschrijving", default=_("No data available")
                ),
                "status_indicator": getattr(
                    statustype_config_mapping.get(s.statustype.url),
                    "status_indicator",
                    None,
                ),
                "status_indicator_text": getattr(
                    statustype_config_mapping.get(s.statustype.url),
                    "status_indicator_text",
                    None,
                ),
                "call_to_action_url": getattr(
                    statustype_config_mapping.get(s.statustype.url),
                    "call_to_action_url",
                    None,
                ),
                "call_to_action_text": getattr(
                    statustype_config_mapping.get(s.statustype.url),
                    "call_to_action_text",
                    None,
                ),
                "description": getattr(
                    statustype_config_mapping.get(s.statustype.url), "description", None
                ),
                "case_link_text": getattr(
                    statustype_config_mapping.get(s.statustype.url),
                    "case_link_text",
                    _("Bekijk aanvraag"),
                ),
            }
            for s in statuses
        ]

    @staticmethod
    def get_case_document_files(case: Zaak, client: ZakenClient) -> List[SimpleFile]:
        if not client:
            return []

        case_info_objects = client.fetch_case_information_objects(case.url)

        # get the information objects for the case objects

        with parallel() as executor:
            info_objects = executor.map(
                fetch_single_information_object_url,
                [case_info.informatieobject for case_info in case_info_objects],
            )

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
                    name=getattr(info_obj, "titel", None),
                    size=info_obj.bestandsomvang,
                    url=reverse(
                        "cases:document_download",
                        kwargs={
                            "object_id": case.uuid,
                            "info_id": info_obj.uuid,
                        },
                    ),
                    created=getattr(case_info_obj, "registratiedatum", None),
                )
            )

        # `registratiedatum` and `titel` should be present, but not guaranteed by schema
        try:
            return sorted(documents, key=lambda doc: doc.created, reverse=True)
        except TypeError:
            try:
                return sorted(
                    documents, key=lambda doc: doc.name
                )  # order ascending b/c alphabetical
            except TypeError:
                return documents

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["case"] = self.case
        return kwargs

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

        zaken_client = build_client_openzaak("zaak")
        if not zaken_client:
            raise Http404

        info_object_uuid = kwargs["info_id"]
        info_object = fetch_single_information_object_uuid(info_object_uuid)
        if not info_object:
            raise Http404

        # check if this info_object belongs to this case
        if not zaken_client.fetch_case_information_objects_for_case_and_info(
            self.case.url, info_object.url
        ):
            raise PermissionDenied()

        # check if this info_object should be visible
        config = OpenZaakConfig.get_solo()
        if not is_info_object_visible(info_object, config.document_max_confidentiality):
            raise PermissionDenied()

        # retrieve and stream content
        content_stream = None
        if client := build_client_openzaak("document"):
            content_stream = client.download_document(info_object.inhoud)

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
            reverse("cases:case_detail", kwargs={"object_id": str(self.case.uuid)})
        )

    def handle_document_upload(self, request, form):
        cleaned_data = form.cleaned_data
        files = cleaned_data["files"]

        created_documents = []

        for file in files:
            title = file.name
            document_type = cleaned_data["type"]
            source_organization = self.case.bronorganisatie

            client = build_client_openzaak("document")
            if client is None:
                return self.handle_document_error(request, file)

            created_document = client.upload_document(
                request.user,
                file,
                title,
                document_type.informatieobjecttype_url,
                source_organization,
            )
            if not created_document:
                return self.handle_document_error(request, file)

            created_relationship = None
            if zaken_client := build_client_openzaak("zaak"):
                created_relationship = zaken_client.connect_case_with_document(
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
            reverse("cases:case_detail", kwargs={"object_id": str(self.case.uuid)})
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["case"] = self.case
        return kwargs

    def get_success_url(self):
        return reverse(
            "cases:case_detail_document_form", kwargs={"object_id": str(self.case.uuid)}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["hxpost_document_action"] = reverse(
            "cases:case_detail_document_form", kwargs=self.kwargs
        )
        return context


class CaseContactFormView(CaseAccessMixin, LogMixin, FormView):
    template_name = "pages/cases/contact_form.html"
    form_class = CaseContactForm

    def post(self, request, *args, **kwargs):
        form = self.get_form()

        if form.is_valid():
            config = OpenKlantConfig.get_solo()

            success = True
            if config.register_email:
                form.cleaned_data[
                    "question"
                ] += f"\n\nCase number: {self.case.identificatie}"
                success = (
                    self.register_by_email(form, config.register_email) and success
                )
            if config.register_contact_moment:
                success = self.register_by_api(form, config) and success

            self.get_result_message(success=success)

            return HttpResponseClientRedirect(
                reverse("cases:case_detail", kwargs={"object_id": str(self.case.uuid)})
            )
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse(
            "cases:case_detail_contact_form", kwargs={"object_id": str(self.case.uuid)}
        )

    def get_result_message(self, success=False):
        if success:
            return messages.add_message(
                self.request, messages.SUCCESS, _("Vraag verstuurd!")
            )
        else:
            return messages.add_message(
                self.request,
                messages.ERROR,
                _("Probleem bij versturen van de vraag."),
            )

    def register_by_email(self, form, recipient_email):
        template = find_template("contactform_registration")

        context = {
            "subject": _("Case: {case_identification}").format(
                case_identification=self.case.identificatie
            ),
            "email": self.request.user.email,
            "phonenumber": self.request.user.phonenumber,
            "question": form.cleaned_data["question"],
            "name": self.request.user.get_full_name(),
        }

        success = template.send_email([recipient_email], context)

        if success:
            self.log_system_action(
                "registered contactmoment by email", user=self.request.user
            )
            return True
        else:
            self.log_system_action(
                "error while registering contactmoment by email",
                user=self.request.user,
            )
            return False

    def register_by_api(self, form, config: OpenKlantConfig):
        assert config.has_api_configuration()

        try:
            ztc = ZaakTypeConfig.objects.filter_case_type(self.case.zaaktype).get()
        except ObjectDoesNotExist:
            ztc = None

        if klanten_client := build_client_openklant("klanten"):
            klant = klanten_client.retrieve_klant(**get_fetch_parameters(self.request))

            if klant:
                self.log_system_action(
                    "retrieved klant for user", user=self.request.user
                )
            else:
                self.log_system_action(
                    "could not retrieve klant for user", user=self.request.user
                )
                data = {
                    "bronorganisatie": config.register_bronorganisatie_rsin,
                    "voornaam": self.request.user.first_name,
                    "voorvoegselAchternaam": self.request.user.infix,
                    "achternaam": self.request.user.last_name,
                    "emailadres": self.request.user.email,
                    "telefoonnummer": self.request.user.phonenumber,
                }
                # registering klanten won't work in e-Suite as it always pulls from BRP (but try anyway and fallback to appending details to tekst if fails)
                klant = klanten_client.create_klant(data)

                if klant:
                    self.log_system_action(
                        "created klant for basic authenticated user",
                        user=self.request.user,
                    )
                else:
                    self.log_system_action(
                        "could not create klant for user", user=self.request.user
                    )
        else:
            self.log_system_action("could not build client for klanten API")

        # create contact moment
        question = form.cleaned_data["question"]
        data = {
            "bronorganisatie": config.register_bronorganisatie_rsin,
            "tekst": question,
            "type": config.register_type,
            "kanaal": "Internet",
            "medewerkerIdentificatie": {
                "identificatie": config.register_employee_id,
            },
        }
        if ztc and ztc.contact_subject_code:
            data["onderwerp"] = ztc.contact_subject_code

        if contactmomenten_client := build_client_openklant("contactmomenten"):
            contactmoment = contactmomenten_client.create_contactmoment(
                data, klant=klant
            )
            if contactmoment:
                self.log_system_action(
                    "registered contactmoment by API", user=self.request.user
                )
                return True
        else:
            self.log_system_action(
                "error while registering contactmoment by API", user=self.request.user
            )
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contact_form"] = self.get_form()
        context["hxpost_contact_action"] = reverse(
            "cases:case_detail_contact_form", kwargs=self.kwargs
        )
        return context
