from typing import Protocol

from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import TemplateView

import requests
import structlog
from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.accounts.models import User
from open_inwoner.accounts.views.mixins import ContactmomentLogMixin
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.openklant.constants import KlantenServiceType
from open_inwoner.openklant.exceptions import KlantAPIError
from open_inwoner.openklant.models import KlantContactMomentAnswer, KlantenSysteemConfig
from open_inwoner.openklant.services import (
    KlantenService,
    OpenKlant2Service,
    Question,
    QuestionsResult,
    QuestionValidator,
    ZaakWithApiGroup,
    eSuiteKlantenService,
    eSuiteVragenService,
)
from open_inwoner.openklant.views.contactform import ContactFormView
from open_inwoner.openklant.wrap import FetchParameters
from open_inwoner.utils.mixins import PaginationMixin
from open_inwoner.utils.views import CommonPageMixin

logger = structlog.stdlib.get_logger(__name__)


class KlantContactMomentAccessMixin(AccessMixin):
    """
    Shared authorisation check

    Base checks:
    - user is authenticated
    - user has a BSN

    # When retrieving a case :
    # - users BSN has a role for this case
    # - case confidentiality is not higher than globally configured
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if not request.user.bsn and not request.user.kvk:
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect(reverse("pages-root"))
        else:
            return super().handle_no_permission()


class VragenService(Protocol):
    def list_questions(
        self,
        fetch_params: FetchParameters,
        user: User,
    ) -> QuestionsResult: ...

    def retrieve_question(
        self,
        fetch_params: FetchParameters,
        question_uuid: str,
        user: User,
    ) -> tuple[Question | None, ZaakWithApiGroup | None]: ...

    def get_fetch_parameters(
        self,
        user: User | None = None,
    ) -> FetchParameters | None: ...


class KlantContactMomentBaseView(
    CommonPageMixin, BaseBreadcrumbMixin, KlantContactMomentAccessMixin, TemplateView
):
    def get_service(self, service_type: KlantenServiceType) -> VragenService | None:
        if service_type == KlantenServiceType.OPENKLANT2:
            try:
                return OpenKlant2Service()
            except ImproperlyConfigured:
                logger.info("OpenKlant2 configuration missing")
        if service_type == KlantenServiceType.ESUITE:
            try:
                return eSuiteVragenService()
            except ImproperlyConfigured:
                logger.info("eSuiteVragenService configuration missing")
            except RuntimeError:
                logger.warning("Failed to build eSuiteVragenService")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["anchors"] = self.get_anchors()
        return ctx

    def get_fetch_params(self, service: VragenService):
        if not (fetch_params := service.get_fetch_parameters(self.request.user)):
            raise ValueError("User has no bsn or kvk attributes")

        return fetch_params


class KlantContactMomentListView(
    PaginationMixin, ContactFormView, KlantContactMomentBaseView
):
    """
    Display "contactmomenten" (questions), and a form (via ContactFormView) to send a new question
    """

    template_name = "pages/contactmoment/list.html"
    paginate_by = 9

    def dispatch(self, request, *args, **kwargs):
        # This page is always accessible to users with BSN/KVK (checked by
        # KlantContactMomentAccessMixin). ContactFormView.dispatch() would gate it on
        # contact_registration_enabled, but that flag only controls whether the embedded
        # form renders - skip it and go straight to the access mixin.
        return super(ContactFormView, self).dispatch(request, *args, **kwargs)

    @cached_property
    def crumbs(self):
        return [(_("Mijn vragen"), reverse("cases:contactmoment_list"))]

    def page_title(self):
        return _("Mijn vragen")

    def get_anchors(self) -> list:
        return [
            ("#contactmomenten", _("Mijn vragen")),
        ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        questions = []
        fetch_error = False
        for service_type in KlantenServiceType:
            service = self.get_service(service_type=service_type)
            if not service:
                continue

            try:
                service_result = service.list_questions(
                    self.get_fetch_params(service),
                    user=self.request.user,
                )
                questions.extend(service_result.questions)
                # One render spans both backends, so incompleteness in either means
                # the combined list is incomplete.
                fetch_error = fetch_error or service_result.is_incomplete
            except KlantAPIError:
                fetch_error = True
                logger.error(
                    "Error fetching questions for service",
                    service_type=service_type.value,
                )
            except Exception:
                fetch_error = True
                logger.exception(
                    "Unkown error fetching questions with Klant service",
                    service_type=service_type.value,
                )

        ctx["partial_results"] = fetch_error

        questions.sort(key=lambda q: q["registered_date"], reverse=True)

        paginator_dict = self.paginate_with_context(questions)
        ctx.update(paginator_dict)

        siteconfig = SiteConfiguration.get_solo()
        klanten_config = KlantenSysteemConfig.get_solo()
        ctx["contactmoment_contact_form_enabled"] = (
            siteconfig.contactmoment_contact_form_enabled
            and klanten_config.contact_registration_enabled
        )

        self.log_contactmoment_list_accessed(questions=questions)

        return ctx


class KlantContactMomentDetailView(ContactmomentLogMixin, KlantContactMomentBaseView):
    template_name = "pages/contactmoment/detail.html"

    @cached_property
    def crumbs(self):
        return [(_("Mijn vragen"), reverse("cases:contactmoment_list"))]

    def page_title(self):
        return f"{_('Mijn vraag')} {self.question['identification']}"

    def get_anchors(self) -> list:
        return [
            ("#contactmomenten-details", _("Details")),
            ("#contactmomenten-vraag", _("Vraag")),
        ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        service: VragenService | None = None
        if KlantenServiceType.ESUITE.value in self.request.path:
            service = self.get_service(service_type=KlantenServiceType.ESUITE)
        elif KlantenServiceType.OPENKLANT2.value in self.request.path:
            service = self.get_service(service_type=KlantenServiceType.OPENKLANT2)

        if not service:
            raise ImproperlyConfigured("Unknown KlantenServiceType")

        try:
            question, zaak_with_api_group = service.retrieve_question(
                self.get_fetch_params(service),
                question_uuid=kwargs["kcm_uuid"],
                user=self.request.user,
            )
        except (KlantAPIError, requests.RequestException) as exc:
            logger.error(
                "Error fetching question detail",
                question_uuid=kwargs.get("kcm_uuid"),
            )
            raise Http404() from exc
        if not question:
            raise Http404()

        self.question = QuestionValidator.validate_python(question)

        ctx["question"] = question
        ctx["zaak"] = getattr(zaak_with_api_group, "zaak", None)
        case_url = (
            reverse(
                "cases:case_detail",
                kwargs={
                    "object_id": str(zaak_with_api_group.zaak.uuid),
                    "api_group_id": zaak_with_api_group.api_group.id,
                },
            )
            if zaak_with_api_group
            else None
        )
        ctx["metrics"] = [
            {
                "label": _("Status"),
                "value": question["status"].capitalize(),
            },
            {
                "label": _("Ingediend op"),
                "value": question["registered_date"],
            },
            {
                "label": _("Vraag nummer"),
                "value": question["identification"],
            },
            {
                "label": _("Contact gehad via"),
                "value": question["channel"].capitalize(),
            },
        ]
        if (origin := self.request.headers.get("Referer")) and reverse(
            "cases:contactmoment_list"
        ) in origin:
            ctx["origin"] = {
                "label": _("Terug naar overzicht"),
                "url": origin,
            }
            if zaak_with_api_group:
                ctx["destination"] = {
                    "label": _("Naar aanvraag"),
                    "url": case_url,
                }
        else:
            ctx["origin"] = {
                "label": _("Terug naar aanvraag"),
                "url": case_url,
            }
            ctx["destination"] = {
                "label": _("Bekijk alle vragen"),
                "url": reverse("cases:contactmoment_list"),
            }

        local_kcm, created = KlantContactMomentAnswer.objects.get_or_create(  # noqa
            user=self.request.user, contactmoment_url=question["api_source_url"]
        )
        if not local_kcm.is_seen:
            local_kcm.is_seen = True
            local_kcm.save()

        self.log_contactmoment_detail_accessed(
            identification=question["identification"]
        )

        return ctx


class KlantContactMomentRedirectView(KlantContactMomentAccessMixin, View):
    """
    Redirect to `KlantContactMomentDetailView` on the basis of contactmoment uuid
    """

    def get(self, request, *args, **kwargs):
        api_service = kwargs.get("api_service")

        match api_service:
            case KlantenServiceType.OPENKLANT2.value:
                question_uuid = self._get_klantcontact_openklant(
                    request, *args, **kwargs
                )
            case KlantenServiceType.ESUITE.value:
                question_uuid = self._get_klantcontactmoment_esuite(
                    request, *args, **kwargs
                )
            case _:
                raise RuntimeError("Unsupported klanten backend")

        return HttpResponseRedirect(
            reverse(
                "cases:contactmoment_detail",
                kwargs={
                    "api_service": api_service,
                    "kcm_uuid": question_uuid,
                },
            )
        )

    def _get_klantcontact_openklant(self, request, *args, **kwargs):
        service: OpenKlant2Service = OpenKlant2Service()
        fetch_params = service.get_fetch_parameters(request.user)

        question_dto, _ = service.retrieve_question(
            fetch_params=fetch_params,
            question_uuid=kwargs.get("uuid"),
            user=request.user,
        )

        if not question_dto:
            raise Http404

        return question_dto.get("api_source_uuid")

    def _get_klantcontactmoment_esuite(self, request, *args, **kwargs):
        vragen_service: VragenService = eSuiteVragenService()
        klanten_service: KlantenService = eSuiteKlantenService()
        fetch_params = klanten_service.get_fetch_parameters(self.request.user)

        klant = klanten_service.retrieve_klant(**fetch_params)
        kcms = vragen_service.retrieve_klantcontactmomenten_for_klant(
            klant
        ).klantcontactmomenten

        if not kcms:
            raise Http404

        contactmoment_uuid = kwargs["uuid"]
        kcm = next(
            (kcm for kcm in kcms if str(kcm.contactmoment.uuid) == contactmoment_uuid),
            None,
        )

        if not kcm:
            raise Http404

        return kcm.uuid
