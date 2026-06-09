import datetime as dt
import os
from dataclasses import dataclass
from typing import Iterable, Protocol, cast

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import (
    ImproperlyConfigured,
    ObjectDoesNotExist,
    PermissionDenied,
)
from django.http import (
    Http404,
    HttpRequest,
    HttpResponseRedirect,
    StreamingHttpResponse,
)
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import FormView, TemplateView

import structlog
from django_htmx.http import HttpResponseClientRedirect
from mail_editor.helpers import find_template
from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.accounts.models import User
from open_inwoner.cms.cases.forms import CaseContactForm, CaseUploadForm
from open_inwoner.components.file_item import FileItem
from open_inwoner.mail.service import send_contact_confirmation_mail
from open_inwoner.openklant.constants import KlantenServiceType
from open_inwoner.openklant.exceptions import KlantAPIError
from open_inwoner.openklant.models import (
    ESuiteKlantConfig,
    KlantenSysteemConfig,
    OpenKlant2Config,
)
from open_inwoner.openklant.services import (
    OpenKlant2Service,
    Question,
    eSuiteKlantenService,
    eSuiteVragenService,
)
from open_inwoner.openzaak.api_models import Status, StatusType, Zaak
from open_inwoner.openzaak.exceptions import ZgwAPIError
from open_inwoner.openzaak.models import (
    OpenZaakConfig,
    ZaakTypeConfig,
    ZaakTypeInformatieObjectTypeConfig,
    ZaakTypeStatusTypeConfig,
    ZGWApiGroupConfig,
)
from open_inwoner.openzaak.services import ZaakDetailData, ZGWService
from open_inwoner.userfeed import hooks
from open_inwoner.utils.glom import glom_multiple
from open_inwoner.utils.time import has_new_elements
from open_inwoner.utils.views import CommonPageMixin

from .mixins import CaseAccessMixin, CaseLogMixin, OuterCaseAccessMixin

logger = structlog.stdlib.get_logger(__name__)


@dataclass
class ZaakContext:
    """Presentation-layer snapshot of a zaak for the detail template."""

    id: str
    identification: str
    initiator: str
    result: str
    result_description: str
    start_date: dt.date
    end_date: dt.date | None
    end_date_planned: dt.date | None
    end_date_legal: dt.date | None
    description: str
    statuses: list[dict]
    end_statustype_data: dict | None
    second_status_preview: StatusType | None
    documents: list
    allowed_file_extensions: list[str]
    new_docs: bool
    questions: list[Question]
    # upload / contact info (from get_upload_info_context)
    case_type_config_description: str
    case_type_document_upload_description: str
    internal_upload_enabled: bool
    external_upload_enabled: bool
    external_upload_url: str
    contact_form_enabled: bool

    @classmethod
    def from_zaak_detail(
        cls,
        zaak: "Zaak",
        zaak_detail: "ZaakDetailData",
        openzaak_config: "OpenZaakConfig",
        documents: list,
        second_status_preview: "StatusType | None",
        end_statustype_data: "dict | None",
        statuses: list[dict],
        questions: list["Question"],
        upload_info: dict,
    ) -> "ZaakContext":
        return cls(
            id=str(zaak.uuid),
            identification=zaak.identification,
            initiator=zaak_detail.initiator,
            result=zaak_detail.result.get("display", ""),
            result_description=zaak_detail.result.get("description", ""),
            start_date=zaak.startdatum,
            end_date=getattr(zaak, "einddatum", None),
            end_date_planned=getattr(zaak, "einddatum_gepland", None),
            end_date_legal=getattr(zaak, "uiterlijke_einddatum_afdoening", None),
            description=zaak.description,
            statuses=statuses,
            end_statustype_data=end_statustype_data,
            second_status_preview=second_status_preview,
            documents=documents,
            allowed_file_extensions=sorted(openzaak_config.allowed_file_extensions),
            new_docs=has_new_elements(
                documents,
                "created",
                dt.timedelta(days=settings.DOCUMENT_RECENT_DAYS),
            ),
            questions=questions,
            **upload_info,
        )


class VragenService(Protocol):
    def list_questions_for_zaak(
        self,
        zaak: Zaak,
        user: User | None = None,
    ) -> Iterable[Question]: ...


class OuterCaseDetailView(
    OuterCaseAccessMixin,
    CommonPageMixin,
    BaseBreadcrumbMixin,
    CaseAccessMixin,
    TemplateView,
):
    template_name = "pages/cases/status_outer.html"
    zaak: Zaak | None = None

    @cached_property
    def crumbs(self):
        # zaak is retrieved via CaseAccessMixin
        if self.zaak:
            return [
                (_("Mijn zaken"), reverse("cases:index")),
                (
                    f"{self.zaak.description} - {_('Status')}",
                    reverse("cases:case_detail", kwargs=self.kwargs),
                ),
            ]
        return [
            (_("Mijn zaken"), reverse("cases:index")),
            (
                f"{_('Zaak')} - {_('Status')}",
                reverse("cases:case_detail", kwargs=self.kwargs),
            ),
        ]

    def page_title(self):
        if self.zaak:
            return f"{self.zaak.description} {self.zaak.identification} - {_('Status')}"
        else:
            return f"{_('Zaak')} - {_('Status')}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["hxget"] = reverse("cases:case_detail_content", kwargs=self.kwargs)
        context["custom_anchors"] = True
        return context

    def get(self, request, *args, **kwargs):
        try:
            ZGWApiGroupConfig.objects.get(pk=self.kwargs["api_group_id"])
        except ZGWApiGroupConfig.DoesNotExist as exc:
            logger.exception("Non-existent ZGWApiGroupConfig passed")
            raise Http404 from exc

        return super().get(request, *args, **kwargs)


class InnerCaseDetailView(
    CaseLogMixin,
    CommonPageMixin,
    BaseBreadcrumbMixin,
    CaseAccessMixin,
    FormView,
):
    template_name = "pages/cases/status_inner.html"
    form_class = CaseUploadForm
    contact_form_class = CaseContactForm
    zaak: Zaak | None = None

    def get_service(self, service_type: KlantenServiceType) -> VragenService | None:
        if service_type == KlantenServiceType.OPENKLANT2:
            try:
                return OpenKlant2Service()
            except Exception:
                logger.warning("Failed to build OpenKlant2 service")
        if service_type == KlantenServiceType.ESUITE:
            try:
                return eSuiteVragenService()
            except Exception:
                logger.warning("Failed to build eSuiteVragenService")

    def store_statustype_mapping(self, zaaktype_identificatie):
        # Filter on ZaakType identificatie: one statustype can be linked to multiple zaaktypes
        # Filter on catalogus service: a zaak could be imported + viewed with different
        # api groups, causing a mismatch in `ZaakTypeStatusTypeConfig.statustype_url`
        configs = list(
            ZaakTypeStatusTypeConfig.objects.filter(
                zaaktype_config__identificatie=zaaktype_identificatie,
                zaaktype_config__catalogus__service=self.api_group.ztc_service,
            )
        )
        if not configs:
            logger.warning(
                "No ZaakTypeStatusTypeConfig found for zaaktype - run zgw_import_data",
                zaaktype_identificatie=zaaktype_identificatie,
                api_group=self.api_group.name,
            )

        self.statustype_config_mapping = {
            config.statustype_url: config for config in configs
        }

    @cached_property
    def crumbs(self):
        # zaak is retrieved via CaseAccessMixin
        if self.zaak:
            return [
                (_("Mijn zaken"), reverse("cases:index")),
                (
                    f"{self.zaak.description} - {_('Status')}",
                    reverse("cases:case_detail", kwargs=self.kwargs),
                ),
            ]
        return [
            (_("Mijn zaken"), reverse("cases:index")),
            (
                f"{_('Zaak')} - {_('Status')}",
                reverse("cases:case_detail", kwargs=self.kwargs),
            ),
        ]

    def page_title(self):
        return f"{self.zaak.description} {self.zaak.identification} - {_('Status')}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # zaak is retrieved via CaseAccessMixin
        if self.zaak:
            self.log_case_detail_accessed(self.zaak)

            openzaak_config = OpenZaakConfig.get_solo()
            api_group = self.api_group
            user_identification = self.request.user.identification
            zaak_detail = ZGWService().get_zaak_detail(
                self.zaak, api_group, user_identification
            )

            self.store_statustype_mapping(self.zaak.zaaktype.identificatie)

            questions = []
            for service_type in KlantenServiceType:
                if service := self.get_service(service_type=service_type):
                    try:
                        service_questions = service.list_questions_for_zaak(
                            self.zaak, user=self.request.user
                        )
                        questions.extend(service_questions)
                    except KlantAPIError:
                        logger.error(
                            "Error fetching questions for service",
                            service_type=service_type.value,
                        )
                    except BaseException:
                        logger.exception(
                            "Unable to fetch questions for service",
                            service_type=service_type.value,
                        )

            questions.sort(key=lambda q: q["registered_date"], reverse=True)

            if len(zaak_detail.statuses) == 1:
                second_status_preview = self.get_second_status_preview(
                    zaak_detail.statustypen
                )
            else:
                second_status_preview = None

            end_statustype_data = self.handle_end_statustype_data(
                status_types_mapping=zaak_detail.status_types_mapping,
                end_statustype=self.handle_end_statustype(
                    zaak_detail.statuses, zaak_detail.statustypen
                ),
            )

            documents = [
                FileItem.from_informatieobject(
                    doc_data.info_obj,
                    doc_data.case_info_obj,
                    reverse(
                        "cases:document_download",
                        kwargs={
                            "object_id": self.zaak.uuid,
                            "info_id": doc_data.info_obj.uuid,
                            "api_group_id": api_group.id,
                        },
                    ),
                )
                for doc_data in zaak_detail.documents
            ]

            hooks.case_status_seen(self.request.user, self.zaak)
            hooks.case_documents_seen(self.request.user, self.zaak)

            zaak_context = ZaakContext.from_zaak_detail(
                zaak=self.zaak,
                zaak_detail=zaak_detail,
                openzaak_config=openzaak_config,
                documents=documents,
                second_status_preview=second_status_preview,
                end_statustype_data=end_statustype_data,
                statuses=self.get_statuses_data(
                    zaak_detail.statuses, self.statustype_config_mapping
                ),
                questions=questions,
                upload_info=self.get_upload_info_context(self.zaak),
            )
            context["zaak"] = zaak_context
            context["anchors"] = self.get_anchors(zaak_detail.statuses, documents)
            context["contact_form"] = self.contact_form_class()
            context["hxpost_contact_action"] = reverse(
                "cases:case_detail_contact_form", kwargs=self.kwargs
            )
            context["hxpost_document_action"] = reverse(
                "cases:case_detail_document_form", kwargs=self.kwargs
            )
            context["metrics"] = [
                {
                    "label": openzaak_config.zaak_identificatie_label,
                    "value": zaak_context.identification,
                },
                {
                    "label": openzaak_config.zaak_start_date_label,
                    "value": zaak_context.start_date,
                },
            ]
            if zaak_context.end_date:
                context["metrics"].append(
                    {
                        "label": openzaak_config.zaak_end_date_label,
                        "value": zaak_context.end_date,
                    },
                )
            else:
                end_date = zaak_context.end_date_legal or zaak_context.end_date_planned
                context["metrics"].append(
                    {
                        "label": openzaak_config.zaak_expected_end_date_label,
                        "value": end_date + dt.timedelta(days=1)
                        if end_date
                        else _("unkown"),
                    }
                )
        else:
            context["zaak"] = None

        return context

    def get_second_status_preview(self, statustypen: list) -> StatusType | None:
        """
        Get the relevant status type to display preview of second zaak status

        Note: we cannot assume that the "second" statustype has the `volgnummer` 2;
              hence we get all statustype_numbers, sort in ascending order, and let
              the "second" statustype be that with `volgnummer == statustype_numbers[1]`
        """
        statustype_numbers = [s.volgnummer for s in statustypen]

        # status_types retrieved via eSuite don't always have a volgnummer
        if not all(statustype_numbers):
            return

        # only 1 statustype for `self.zaak`
        # (this scenario is blocked by openzaak, but not part of the zgw standard)
        if len(statustype_numbers) < 2:
            logger.info(
                "zaak has only one statustype",
                case_identificatie=self.zaak.identification,
                case_uuid=self.zaak.uuid,
            )
            return

        statustype_numbers.sort()

        return next(
            filter(
                lambda s: s.volgnummer == statustype_numbers[1] and not s.is_eindstatus,
                statustypen,
            ),
            None,
        )

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
        # because in that zaak the end status data is already included in `statuses`
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
    ):
        """
        Prepare data about end statustype for use in context/template
        """
        end_statustype_data = None
        if not status_types_mapping.get(end_statustype.url):
            end_statustype_data = {
                "label": (
                    end_statustype.statustekst
                    or end_statustype.omschrijving
                    or _("No data available")
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
            ZaakTypeInformatieObjectTypeConfig.objects.filter_enabled_for_zaak_type(
                self.zaak.zaaktype
            ).exists()
        )
        logger.info(
            "File upload status for zaak (enabled/disabled)",
            case_identificatie=self.zaak.identification,
            case_uuid=self.zaak.uuid,
            case_upload_enabled=case_upload_enabled,
        )
        return case_upload_enabled

    @property
    def is_file_upload_enabled_for_statustype(self) -> bool:
        try:
            enabled_for_status_type = self.statustype_config_mapping[
                self.zaak.status.statustype.url
            ].document_upload_enabled
        except AttributeError:
            logger.exception(
                "Could not retrieve status type for zaak; the status has not been resolved to a ZGW model object",
                case_identificatie=self.zaak.identification,
                case_uuid=self.zaak.uuid,
            )
            return True
        except KeyError:
            logger.exception(
                "Could not retrieve status type config for url",
                statustype_url=self.zaak.status.statustype.url,
            )
            return True
        logger.info(
            "File upload for zaak statustype (enabled/disabled)",
            case_url=self.zaak.url,
            status_type=self.zaak.status.statustype,
            file_upload_enabled=enabled_for_status_type,
        )
        return enabled_for_status_type

    @property
    def is_internal_file_upload_enabled(self) -> bool:
        return (
            self.is_file_upload_enabled_for_case_type
            and self.is_file_upload_enabled_for_statustype
        )

    def get_upload_info_context(self, zaak: Zaak):
        if not zaak:
            return {}

        klanten_config = KlantenSysteemConfig.get_solo()

        case_type_config_description = ""
        case_type_document_upload_description = ""
        external_upload_enabled = False
        external_upload_url = ""
        contact_form_enabled = False

        try:
            ztc = ZaakTypeConfig.objects.filter_zaak_type(zaak.zaaktype).get()
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
                    statustype_url=zaak.status.statustype.url
                )
            # zaak has no status, or statustype config not found
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
            and not getattr(self.zaak, "einddatum", None),
            "external_upload_enabled": external_upload_enabled
            and not getattr(self.zaak, "einddatum", None),
            "external_upload_url": external_upload_url,
            "contact_form_enabled": (
                contact_form_enabled and klanten_config.contact_registration_enabled
            ),
        }

    @staticmethod
    def get_statuses_data(
        statuses: list[Status],
        statustype_config_mapping: dict,
    ) -> list[dict]:
        statuses_data = []

        for status in statuses:
            config = statustype_config_mapping.get(status.statustype.url)
            if config is None and status.statustype.url:
                logger.warning(
                    "No ZaakTypeStatusTypeConfig for statustype URL",
                    statustype_url=status.statustype.url,
                )

            statuses_data.append(
                {
                    "date": status.datum_status_gezet,
                    "label": glom_multiple(
                        status,
                        ("statustype.statustekst", "statustype.omschrijving"),
                        default=_("Nieuwe aanvraag"),
                    ),
                    "status_indicator": getattr(
                        statustype_config_mapping.get(status.statustype.url),
                        "status_indicator",
                        None,
                    ),
                    "status_indicator_text": getattr(
                        statustype_config_mapping.get(status.statustype.url),
                        "status_indicator_text",
                        None,
                    ),
                    "call_to_action_url": getattr(
                        statustype_config_mapping.get(status.statustype.url),
                        "call_to_action_url",
                        None,
                    ),
                    "call_to_action_text": getattr(
                        statustype_config_mapping.get(status.statustype.url),
                        "call_to_action_text",
                        None,
                    ),
                    "description": (
                        config.description.html
                        if (
                            config := statustype_config_mapping.get(
                                status.statustype.url
                            )
                        )
                        and config.description
                        else ""
                    ),
                    "case_link_text": getattr(
                        statustype_config_mapping.get(status.statustype.url),
                        "case_link_text",
                        _("Bekijk aanvraag"),
                    ),
                }
            )

        return statuses_data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["zaak"] = self.zaak
        return kwargs

    def get_anchors(self, statuses, documents):
        anchors = [["#title", _("Gegevens")]]

        if statuses:
            anchors.append(["#statuses", _("Status")])

        if documents:
            anchors.append(["#documents", _("Documenten")])

        return anchors


class CaseDocumentDownloadView(CaseLogMixin, CaseAccessMixin, View):
    def get(self, request, *args, **kwargs):
        if not self.zaak:
            raise Http404

        try:
            api_group = ZGWApiGroupConfig.objects.get(pk=self.kwargs["api_group_id"])
        except ZGWApiGroupConfig.DoesNotExist as exc:
            logger.exception("Non-existent ZGWApiGroupConfig passed")
            raise Http404 from exc

        info_object_uuid = kwargs["info_id"]
        service = ZGWService()
        try:
            info_object = service.fetch_information_object_by_uuid(
                info_object_uuid, api_group
            )
        except ZgwAPIError as exc:
            raise Http404 from exc

        # check if this info_object belongs to this zaak
        try:
            zaak_info_objects = (
                service.fetch_zaak_information_objects_for_zaak_and_info(
                    self.zaak.url, info_object.url, api_group
                )
            )
        except ZgwAPIError as exc:
            raise Http404 from exc
        if not zaak_info_objects:
            raise PermissionDenied()

        # check if this info_object should be visible
        config = OpenZaakConfig.get_solo()
        if not service._is_info_object_visible(
            info_object,
            config.document_max_confidentiality,
            config.document_visible_statuses,
        ):
            raise PermissionDenied()

        # retrieve and stream content
        try:
            content_stream = service.download_document(info_object.inhoud, api_group)
        except ZgwAPIError as exc:
            raise Http404 from exc

        # Validate the actual content length matches the expected size. Note that this
        # is best-effort: if somehow content-length is malformed or bestandsomvang is
        # missing, we revert to just streaming the file and hoping for the best (the
        # behavior prior to introducing this check).
        actual_content_length = content_stream.headers.get("Content-Length")
        try:
            parsed_content_length = (
                int(actual_content_length) if actual_content_length else None
            )
        except (ValueError, TypeError):
            logger.warning(
                "Document content-length header is malformed",
                info_object_uuid=info_object_uuid,
                actual_content_length=actual_content_length,
            )
            parsed_content_length = None

        if (
            parsed_content_length is not None
            and info_object.bestandsomvang is not None
            and parsed_content_length != info_object.bestandsomvang
        ):
            logger.warning(
                "Document size mismatch",
                info_object_uuid=info_object_uuid,
                expected_size=info_object.bestandsomvang,
                actual_size=parsed_content_length,
            )
            messages.error(
                request,
                _(
                    "Het document kon niet worden gedownload vanwege een fout in de gegevens."
                ),
            )
            return HttpResponseRedirect(
                reverse(
                    "cases:case_detail",
                    kwargs={
                        "api_group_id": self.kwargs["api_group_id"],
                        "object_id": self.zaak.uuid,
                    },
                )
            )

        self.log_case_document_downloaded(self.zaak, info_object.bestandsnaam)

        headers = {
            "Content-Disposition": f'attachment; filename="{info_object.bestandsnaam}"',
            "Content-Type": info_object.formaat,
        }
        if info_object.bestandsomvang is not None:
            headers["Content-Length"] = str(info_object.bestandsomvang)

        response = StreamingHttpResponse(content_stream, headers=headers)
        return response

    def handle_no_permission(self):
        # plain error and no redirect
        raise PermissionDenied()


class CaseDocumentUploadFormView(CaseAccessMixin, CaseLogMixin, FormView):
    template_name = "pages/cases/document_form.html"
    form_class = CaseUploadForm

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if form.is_valid() and not getattr(self.zaak, "einddatum", None):
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
                    "object_id": str(self.zaak.uuid),
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
        service = ZGWService()

        for file in files:
            title = os.path.splitext(file.name)[0] or file.name
            document_type = cleaned_data["type"]
            source_organization = self.zaak.bronorganisatie

            try:
                created_document = service.upload_document(
                    request.user,
                    file,
                    title,
                    document_type.informatieobjecttype_url,
                    source_organization,
                    api_group,
                )
            except ZgwAPIError:
                return self.handle_document_error(request, file)

            try:
                service.connect_case_with_document(
                    self.zaak.url, created_document.get("url"), api_group
                )
            except ZgwAPIError:
                return self.handle_document_error(request, file)

            self.log_case_document_uploaded(self.zaak, file.name)
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
                    "object_id": str(self.zaak.uuid),
                    "api_group_id": self.kwargs["api_group_id"],
                },
            )
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["zaak"] = self.zaak
        return kwargs

    def get_success_url(self):
        return reverse(
            "cases:case_detail_document_form",
            kwargs={
                "object_id": str(self.zaak.uuid),
                "api_group_id": self.kwargs["api_group_id"],
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["hxpost_document_action"] = reverse(
            "cases:case_detail_document_form", kwargs=self.kwargs
        )
        return context


class CaseContactFormView(CaseAccessMixin, CaseLogMixin, FormView):
    template_name = "pages/cases/contact_form.html"
    form_class = CaseContactForm

    def post(self, request, *args, **kwargs):
        try:
            api_group = ZGWApiGroupConfig.objects.get(pk=self.kwargs["api_group_id"])
        except ZGWApiGroupConfig.DoesNotExist as exc:
            logger.exception("Non-existent ZGWApiGroupConfig passed")
            raise Http404 from exc

        form = self.get_form()

        if form.is_valid():
            klant_config = KlantenSysteemConfig.get_solo()

            email_success = False
            api_success = False
            send_confirmation = False

            if klant_config.register_contact_email:
                form.cleaned_data["question"] += (
                    f"\n\nCase number: {self.zaak.identificatie}"
                )
                email_success = self.register_by_email(
                    form, klant_config.register_contact_email
                )
                send_confirmation = email_success

            if klant_config.register_contact_via_api:
                api_success = self.register_by_api(form, api_group)
                if api_success:
                    send_confirmation = klant_config.send_email_confirmation
                # else keep the send_confirmation if email set it

            if send_confirmation:
                subject = _("zaak: {case_identification}").format(
                    case_identification=self.zaak.identificatie
                )
                send_contact_confirmation_mail(self.request.user.email, subject)

            self.set_result_message(email_success or api_success)

            return HttpResponseClientRedirect(
                reverse(
                    "cases:case_detail",
                    kwargs={
                        "object_id": str(self.zaak.uuid),
                        "api_group_id": self.kwargs["api_group_id"],
                    },
                )
            )
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse(
            "cases:case_detail_contact_form", kwargs={"object_id": str(self.zaak.uuid)}
        )

    def set_result_message(self, success: bool):
        if success:
            messages.add_message(self.request, messages.SUCCESS, _("Vraag verstuurd!"))
        else:
            messages.add_message(
                self.request,
                messages.ERROR,
                _("Probleem bij versturen van de vraag."),
            )

    def register_by_email(self, form, recipient_email):
        template = find_template("contactform_registration")

        context = {
            "subject": _("zaak: {case_identification}").format(
                case_identification=self.zaak.identificatie
            ),
            "email": self.request.user.email,
            "phonenumber": self.request.user.phonenumber,
            "question": form.cleaned_data["question"],
            "name": self.request.user.get_full_name(),
        }

        success = template.send_email([recipient_email], context)

        self.log_contactmoment_for_zaak_registered_by_email(success)
        return bool(success)

    def register_by_api(self, form, api_group: ZGWApiGroupConfig):
        if not api_group.klant_backend:
            return

        match api_group.klant_backend:
            case KlantenServiceType.ESUITE.value:
                return self._register_via_esuite(
                    form, config=ESuiteKlantConfig.get_solo()
                )
            case KlantenServiceType.OPENKLANT2.value:
                return self._register_via_openklant(
                    form, config=OpenKlant2Config.get_solo()
                )
            case _:
                logger.error(
                    "Got non-existent klanten backend",
                    klanten_backend=api_group.klant_backend,
                )

    def _register_via_openklant(self, form, config: OpenKlant2Config) -> bool:
        user = cast(User, self.request.user)
        service = OpenKlant2Service(config=config)

        partij, _ = service.get_or_create_partij_for_user(user)

        if not partij:
            return False

        cleaned_data = form.cleaned_data
        question = cleaned_data["question"]

        question = service.create_question_for_zaak(
            partij_uuid=partij["uuid"],
            question=question,
            zaak=self.zaak,
        )

        return bool(question)

    def _register_via_esuite(self, form, config: ESuiteKlantConfig):
        if not config.has_api_configuration:
            raise ImproperlyConfigured("Missing eSuite API configuration")

        try:
            ztc = ZaakTypeConfig.objects.filter_zaak_type(self.zaak.zaaktype).get()
        except ObjectDoesNotExist:
            ztc = None

        klant = None
        user = cast(User, self.request.user)
        try:
            service = eSuiteKlantenService(config=config)
        except (ImproperlyConfigured, RuntimeError):
            self.log_system_action("could not build client for klanten API")
        else:
            try:
                fetch_params = service.get_fetch_parameters(user)
                klant, created = service.get_or_create_klant(
                    fetch_params=fetch_params, user=user
                )
            except KlantAPIError:
                logger.error("Error retrieving/creating klant for contactmoment")

        # create contact moment
        question = form.cleaned_data["question"]
        data = {
            "bronorganisatie": config.register_bronorganisatie_rsin,
            "tekst": question,
            "type": config.register_type,
            "kanaal": config.register_channel,
        }
        if employee_id := config.register_employee_id:
            data["medewerkerIdentificatie"] = {"identificatie": employee_id}
        if ztc and ztc.contact_subject_code:
            data["onderwerp"] = ztc.contact_subject_code

        try:
            service = eSuiteVragenService(config=config)
        except ImproperlyConfigured:
            logger.error("Failed to build eSuiteVragenService")
            return

        try:
            contactmoment = service.create_contactmoment(data, klant=klant)
        except KlantAPIError:
            logger.error("Error creating contactmoment")
            self.log_contactmoment_for_zaak_registered_by_api(
                contactmoment_success=False
            )
            messages.error(
                request=self.request,
                message=_("Your question could not be saved. Please try again later."),
            )
            return False

        try:
            objectcontactmoment = service.create_objectcontactmoment(
                contactmoment, self.zaak
            )
        except KlantAPIError:
            logger.error("Error creating objectcontactmoment")
            objectcontactmoment = None

        self.log_contactmoment_for_zaak_registered_by_api(
            contactmoment_success=True,
            objectcontactmoment_success=bool(objectcontactmoment),
        )

        # We'll mark this call as successful if the cotactmoment is created, independent of
        # whether we've successfully associated the contactmoment with the zaak, because we
        # still want the notification email to be sent.
        return True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contact_form"] = self.get_form()
        context["hxpost_contact_action"] = reverse(
            "cases:case_detail_contact_form", kwargs=self.kwargs
        )
        return context


class LegacyCaseDetailHandler(View):
    """Redirect the legacy zaak detail to the current version with ZGW API group ref."""

    def get(
        self,
        request: HttpRequest,
        object_id: str,
    ):
        redirect_url = None
        match ZGWApiGroupConfig.objects.count():
            case 1:
                target_api_group = ZGWApiGroupConfig.objects.get()
                redirect_url = reverse(
                    "cases:case_detail",
                    kwargs={
                        "api_group_id": target_api_group.id,
                        "object_id": object_id,
                    },
                )
            case count if count > 1:
                messages.add_message(
                    request,
                    messages.ERROR,
                    _(
                        "The link you clicked on has expired. Please find your zaak in the"
                        " list below."
                    ),
                )
                logger.warning(
                    "Could not automatically handle legacy zaak detail URL due to multiple"
                    " ZGWApiGroupConfig objects"
                )
                redirect_url = reverse("cases:index")
            case 0:
                # This is an invariant violation: there should always be at least
                # one ZGWApiGroupConfig.
                logger.error(
                    "Legacy redirect invoked without any configured API groups"
                )
                raise Http404

        return HttpResponseRedirect(redirect_url)
