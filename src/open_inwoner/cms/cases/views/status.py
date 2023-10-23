import dataclasses
from collections import defaultdict
from typing import List, Optional

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

from open_inwoner.openklant.models import OpenKlantConfig
from open_inwoner.openklant.wrap import (
    create_contactmoment,
    create_klant,
    fetch_klant_for_bsn,
)
from open_inwoner.openzaak.api_models import Status, Zaak
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
    StatusTranslation,
    ZaakTypeConfig,
    ZaakTypeInformatieObjectTypeConfig,
    ZaakTypeStatusTypeConfig,
)
from open_inwoner.openzaak.utils import get_role_name_display, is_info_object_visible
from open_inwoner.utils.translate import TranslationLookup
from open_inwoner.utils.views import CommonPageMixin, LogMixin

from ..forms import CaseContactForm, CaseUploadForm
from .mixins import CaseAccessMixin, CaseLogMixin, OuterCaseAccessMixin


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
    case: Zaak = None

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

            documents = self.get_case_document_files(self.case)

            statuses = fetch_status_history(self.case.url)

            statustype_config_mapping = {
                zaaktype_statustype.statustype_url: zaaktype_statustype
                for zaaktype_statustype in ZaakTypeStatusTypeConfig.objects.all()
            }

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
                "id": str(self.case.uuid),
                "identification": self.case.identification,
                "initiator": self.get_initiator_display(self.case),
                "result": self.get_result_display(self.case),
                "start_date": self.case.startdatum,
                "end_date": getattr(self.case, "einddatum", None),
                "end_date_planned": getattr(self.case, "einddatum_gepland", None),
                "end_date_legal": getattr(
                    self.case, "uiterlijke_einddatum_afdoening", None
                ),
                "description": self.case.zaaktype.omschrijving,
                "statuses": self.get_statuses_data(
                    statuses, status_translate, statustype_config_mapping
                ),
                "documents": documents,
                "allowed_file_extensions": sorted(config.allowed_file_extensions),
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

    def get_upload_info_context(self, case: Zaak):
        if not case:
            return {}

        open_klant_config = OpenKlantConfig.get_solo()

        internal_upload_enabled = (
            ZaakTypeInformatieObjectTypeConfig.objects.filter_enabled_for_case_type(
                case.zaaktype
            ).exists()
        )

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
                case_type_document_upload_description = (
                    zt_statustype_config.document_upload_description
                )
            except ObjectDoesNotExist:
                pass

        return {
            "case_type_config_description": case_type_config_description,
            "case_type_document_upload_description": case_type_document_upload_description,
            "internal_upload_enabled": internal_upload_enabled
            and not getattr(self.case, "einddatum", None),
            "external_upload_enabled": external_upload_enabled
            and not getattr(self.case, "einddatum", None),
            "external_upload_url": external_upload_url,
            "contact_form_enabled": (
                contact_form_enabled and open_klant_config.has_register()
            ),
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

    def get_statuses_data(
        self,
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
            }
            for s in statuses
        ]

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


class CaseDocumentUploadFormView(CaseAccessMixin, LogMixin, FormView):
    template_name = "pages/cases/document_form.html"
    form_class = CaseUploadForm

    def post(self, request, *args, **kwargs):
        form = self.get_form()

        if form.is_valid() and not getattr(self.case, "einddatum", None):
            return self.handle_document_upload(request, form)
        return self.form_invalid(form)

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

                return HttpResponseClientRedirect(
                    reverse(
                        "cases:case_detail", kwargs={"object_id": str(self.case.uuid)}
                    )
                )

        # fail uploading the document or connecting it to the zaak
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

        klant = fetch_klant_for_bsn(self.request.user.bsn)
        if klant:
            self.log_system_action(
                "retrieved klant for BSN-user", user=self.request.user
            )
        else:
            self.log_system_action(
                "could not retrieve klant for BSN-user", user=self.request.user
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
            klant = create_klant(data)
            if klant:
                self.log_system_action(
                    "created klant for basic authenticated user",
                    user=self.request.user,
                )
            else:
                self.log_system_action(
                    "could not create klant for BSN-user", user=self.request.user
                )

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

        contactmoment = create_contactmoment(data, klant=klant)

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
