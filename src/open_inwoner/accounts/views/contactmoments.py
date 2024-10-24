import logging
from datetime import datetime
from typing import Iterable, NotRequired, Protocol, TypedDict

from django.contrib.auth.mixins import AccessMixin
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

from glom import glom
from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.accounts.models import User
from open_inwoner.openklant.api_models import KlantContactMoment
from open_inwoner.openklant.clients import (
    build_contactmomenten_client,
    build_klanten_client,
)
from open_inwoner.openklant.constants import Status
from open_inwoner.openklant.models import (
    ContactFormSubject,
    KlantContactMomentAnswer,
    OpenKlantConfig,
)
from open_inwoner.openklant.views.contactform import ContactFormView
from open_inwoner.openklant.wrap import (
    FetchParameters,
    contactmoment_has_new_answer,
    fetch_klantcontactmoment,
    fetch_klantcontactmomenten,
    get_fetch_parameters,
    get_kcm_answer_mapping,
)
from open_inwoner.openzaak.clients import MultiZgwClientProxy
from open_inwoner.openzaak.models import ZGWApiGroupConfig
from open_inwoner.utils.mixins import PaginationMixin
from open_inwoner.utils.views import CommonPageMixin

logger = logging.getLogger(__name__)


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


class KCMDict(TypedDict):
    registered_date: datetime
    channel: str
    text: str
    url: str
    case_url: str | None
    identificatie: str
    type: str
    onderwerp: str
    status: str
    antwoord: str
    new_answer_available: bool


class QuestionAnswerService(Protocol):

    def list_questions(
        self, fetch_params: FetchParameters, user: User
    ) -> Iterable[KCMDict]: ...

    def retrieve_question(
        self, fetch_params: FetchParameters, question_uuid: str, user: User
    ) -> KCMDict | None: ...


class ContactMomentenService(QuestionAnswerService):
    @staticmethod
    def _get_kcm_subject(
        kcm: KlantContactMoment,
    ) -> str | None:
        """
        Determine the subject (`onderwerp`) of a `KlantContactMoment.contactmoment`:
            1. replace e-suite subject code with corresponding OIP configured subject or
            2. return the first OIP subject if multiple subjects are mapped to the same
               e-suite code or
            3. return the the e-suite subject code if no mapping exists
        """
        e_suite_subject_code = getattr(kcm.contactmoment, "onderwerp", "")

        try:
            subject = ContactFormSubject.objects.get(subject_code=e_suite_subject_code)
        except ContactFormSubject.MultipleObjectsReturned as exc:
            logger.warning(
                "Multiple OIP subjects mapped to the same e-suite subject code for ",
                "contactmoment %s; using the first one",
                kcm.contactmoment.url,
                exc_info=exc,
            )
            return ContactFormSubject.objects.first().subject
        except ContactFormSubject.DoesNotExist as exc:
            logger.warning(
                "Could not determine OIP subject for contactmoment %s; "
                "falling back on e-suite subject code ('onderwerp')",
                kcm.contactmoment.url,
                exc_info=exc,
            )
            return e_suite_subject_code

        return subject.subject

    @staticmethod
    def _get_kcm_data(
        kcm: KlantContactMoment,
        local_kcm_mapping: dict[str, KlantContactMomentAnswer] | None = None,
    ) -> KCMDict:
        if isinstance(kcm.contactmoment, str):
            raise ValueError

        data: KCMDict = {
            "registered_date": kcm.contactmoment.registratiedatum,
            "channel": kcm.contactmoment.kanaal.title(),
            "text": kcm.contactmoment.tekst,
            "url": reverse("cases:contactmoment_detail", kwargs={"kcm_uuid": kcm.uuid}),
            "case_url": None,
            "onderwerp": ContactMomentenService._get_kcm_subject(kcm) or "",
            # eSuite extra
            "identificatie": kcm.contactmoment.identificatie,
            "type": kcm.contactmoment.type,
            "status": Status.safe_label(kcm.contactmoment.status, _("Onbekend")),
            "antwoord": kcm.contactmoment.antwoord,
            "new_answer_available": contactmoment_has_new_answer(
                kcm.contactmoment, local_kcm_mapping=local_kcm_mapping
            ),
        }

        return data

    def list_questions(
        self, fetch_params: FetchParameters, user: User
    ) -> Iterable[KCMDict]:
        kcms = fetch_klantcontactmomenten(**fetch_params)

        klant_config = OpenKlantConfig.get_solo()
        if exclude_range := klant_config.exclude_contactmoment_kanalen:
            kcms = [
                item
                for item in kcms
                if glom(item, "contactmoment.kanaal") not in exclude_range
            ]

        contactmomenten = [
            self._get_kcm_data(
                kcm,
                local_kcm_mapping=get_kcm_answer_mapping(
                    [kcm.contactmoment for kcm in kcms], user
                ),
            )
            for kcm in kcms
        ]
        return contactmomenten

    def retrieve_question(
        self, fetch_params: FetchParameters, question_uuid: str, user: User
    ) -> KCMDict | None:
        if not (kcm := fetch_klantcontactmoment(question_uuid, **fetch_params)):
            return None

        local_kcm, is_created = KlantContactMomentAnswer.objects.get_or_create(  # noqa
            user=user, contactmoment_url=kcm.contactmoment.url
        )
        if not local_kcm.is_seen:
            local_kcm.is_seen = True
            local_kcm.save()

        zaak = None
        case_url = None
        zaak = None
        if client := build_contactmomenten_client():
            ocm = client.retrieve_objectcontactmoment(kcm.contactmoment, "zaak")
            if ocm and ocm.object_type == "zaak":
                zaak_url = ocm.object
                groups = list(ZGWApiGroupConfig.objects.all())
                proxy = MultiZgwClientProxy([group.zaken_client for group in groups])
                proxy_response = proxy.fetch_case_by_url_no_cache(zaak_url)
                cases_found = proxy_response.truthy_responses
                if (case_count := len(cases_found)) == 0:
                    logger.error(
                        "Unable to find matched contactmomenten zaak in any zgw backend"
                    )
                else:
                    zaak, client = cases_found[0].result, cases_found[0].client
                    group = ZGWApiGroupConfig.objects.resolve_group_from_hints(
                        client=client
                    )
                    case_url = reverse(
                        "cases:case_detail",
                        kwargs={
                            "object_id": str(zaak.uuid),
                            "api_group_id": group.id,
                        },
                    )
                    if case_count > 1:
                        # In principle this should not happen, a zaak should be stored in
                        # exactly one backend. But: https://www.xkcd.com/2200/
                        # We should at least receive a ping if this happens.
                        logger.error("Found one zaak in multiple backends")

        data = self._get_kcm_data(kcm)
        data["case_url"] = case_url
        return data


class KlantContactMomentBaseView(
    CommonPageMixin, BaseBreadcrumbMixin, KlantContactMomentAccessMixin, TemplateView
):
    def get_service(self) -> QuestionAnswerService:
        return ContactMomentenService()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["anchors"] = self.get_anchors()
        return ctx

    @property
    def fetch_params(self):
        if not (
            fetch_params := get_fetch_parameters(
                self.request, use_vestigingsnummer=True
            )
        ):
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
        service = self.get_service()
        ctx["contactmomenten"] = service.list_questions(
            self.fetch_params, user=self.request.user
        )
        paginator_dict = self.paginate_with_context(ctx["contactmomenten"])
        ctx.update(paginator_dict)
        return ctx


class KlantContactMomentDetailView(KlantContactMomentBaseView):
    template_name = "pages/contactmoment/detail.html"

    @cached_property
    def crumbs(self):
        return [(_("Mijn vragen"), reverse("cases:contactmoment_list"))]

    def page_title(self):
        return _("Mijn vraag")

    def get_anchors(self) -> list:
        return [
            ("#contactmomenten-details", _("Details")),
            ("#contactmomenten-vraag", _("Vraag")),
        ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        service = self.get_service()

        kcm = service.retrieve_question(
            self.fetch_params, kwargs["kcm_uuid"], user=self.request.user
        )
        if not kcm:
            raise Http404()

        local_kcm, created = KlantContactMomentAnswer.objects.get_or_create(  # noqa
            user=self.request.user, contactmoment_url=kcm["url"]
        )
        if not local_kcm.is_seen:
            local_kcm.is_seen = True
            local_kcm.save()

        contactmoment: KCMDict = self.get_kcm_data(kcm)
        ctx["contactmoment"] = contactmoment
        ctx["metrics"] = [
            {
                "label": _("Status: "),
                "value": contactmoment["status"],
            },
            {
                "label": _("Ingediend op: "),
                "value": contactmoment["registered_date"],
            },
            {
                "label": _("Vraag nummer: "),
                "value": contactmoment["identificatie"],
            },
            {
                "label": _("Contact gehad via: "),
                "value": contactmoment["channel"],
            },
        ]
        origin = self.request.headers.get("Referer")
        if origin and reverse("cases:contactmoment_list") in origin:
            ctx["origin"] = {
                "label": _("Terug naar overzicht"),
                "url": origin,
            }
            if kcm["case_url"]:
                ctx["destination"] = {
                    "label": _("Naar aanvraag"),
                    "url": kcm["case_url"],
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
        return ctx


class KlantContactMomentRedirectView(KlantContactMomentAccessMixin, View):
    """
    Redirect to `KlantContactMomentDetailView` on the basis of contactmoment uuid
    """

    def get(self, request, *args, **kwargs):
        klanten_client = build_klanten_client()
        contactmoment_client = build_contactmomenten_client()

        klant = klanten_client.retrieve_klant(**get_fetch_parameters(self.request))
        kcms = contactmoment_client.retrieve_klantcontactmomenten_for_klant(klant)

        if not kcms:
            raise Http404

        contactmoment_uuid = kwargs["uuid"]
        kcm = next(
            kcm for kcm in kcms if str(kcm.contactmoment.uuid) == contactmoment_uuid
        )

        if not kcm:
            raise Http404

        return HttpResponseRedirect(
            reverse("cases:contactmoment_detail", kwargs={"kcm_uuid": kcm.uuid})
        )
