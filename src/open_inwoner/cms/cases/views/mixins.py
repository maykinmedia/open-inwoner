from __future__ import annotations

from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.http import Http404, HttpRequest
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _

import structlog

from open_inwoner.cms.cases.metrics import (
    case_contact_form_registrations,
    case_detail_views,
    case_document_downloads,
    case_document_uploads,
    case_list_views,
)
from open_inwoner.openzaak.api_models import Zaak
from open_inwoner.openzaak.models import ZGWApiGroupConfig
from open_inwoner.openzaak.services import ZaakNotFound, ZGWService
from open_inwoner.openzaak.types import UniformCase
from open_inwoner.utils.views import LogMixin

logger = structlog.stdlib.get_logger(__name__)


class CaseLogMixin(LogMixin):
    request: HttpRequest

    def log_case_list_accessed(self, cases: list[dict]):
        case_ids = [case["identification"] for case in cases]

        self.log_user_action(
            self.request.user,
            _("Zaken bekeken: {zaken}").format(zaken=", ".join(case_ids)),
        )
        case_list_views.add(1, {"num_cases_viewed": len(case_ids)})

    def log_case_detail_accessed(self, case: UniformCase):
        self.log_user_action(
            self.request.user,
            _("Zaak bekeken: {case}").format(case=case.identification),
        )
        case_detail_views.add(1)

    def log_case_document_downloaded(self, case: UniformCase, filename: str):
        self.log_user_action(
            self.request.user,
            _("Document van zaak gedownload {case}: {filename}").format(
                case=case.identification,
                filename=filename,
            ),
        )
        case_document_downloads.add(1)

    def log_case_document_uploaded(self, case: UniformCase, filename: str):
        self.log_user_action(
            self.request.user,
            _("Document was uploaded for {case}: {filename}").format(
                case=case.identification,
                filename=filename,
            ),
        )
        case_document_uploads.add(1)

    def log_contactmoment_for_zaak_registered_by_email(self, success: bool):
        if success:
            msg = "registered contactmoment by email"
        else:
            msg = "error while registering contactmoment by email"

        self.log_system_action(msg, user=self.request.user)
        case_contact_form_registrations.add(1, {"channel": "email", "success": success})

    def log_contactmoment_for_zaak_registered_by_api(
        self,
        contactmoment_success: bool,
        objectcontactmoment_success: bool | None = None,
    ):
        success = contactmoment_success and (
            objectcontactmoment_success is None or objectcontactmoment_success
        )

        if contactmoment_success:
            msg = "registered contactmoment by API"
        else:
            msg = "error while registering contactmoment by API"

        self.log_system_action(msg, user=self.request.user)

        if objectcontactmoment_success is not None:
            if objectcontactmoment_success:
                msg = "registered objectcontactmoment by API"
            else:
                msg = "error linking objectcontactmoment to contactmoment by API"

            self.log_system_action(msg, user=self.request.user)

        case_contact_form_registrations.add(1, {"channel": "api", "success": success})


class CaseAccessMixin(AccessMixin):
    """
    Shared authorisation check

    Base checks:
    - user is authenticated
    - user has a BSN or KvK number

    When retrieving a case :
    - users BSN/KVK has a role for this case
    - case confidentiality is not higher than globally configured
    """

    zaak: Zaak | None = None
    api_group: ZGWApiGroupConfig | None = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            logger.info("CaseAccessMixin - permission denied: user not authenticated")
            return self.handle_no_permission()

        user_identification = request.user.identification
        if not user_identification:
            logger.info(
                "CaseAccessMixin - permission denied: user doesn't have a bsn or kvk number"
            )
            return self.handle_no_permission()

        is_retrieving_case = (api_group_id := self.kwargs.get("api_group_id")) and (
            object_id := self.kwargs.get("object_id")
        )
        if is_retrieving_case:
            try:
                api_group = ZGWApiGroupConfig.objects.get(pk=api_group_id)
            except ZGWApiGroupConfig.DoesNotExist as exc:
                logger.exception("Non-existent ZGWApiGroupConfig passed")
                raise Http404 from exc

            try:
                result = ZGWService().check_zaak_access(
                    object_id, user_identification, api_group
                )
            except ZaakNotFound:
                # TODO: distinguish between temporary API failures and genuine 404 when
                # the refactoring of error-handling is complete (GH #2142)
                pass
            else:
                if result is None:
                    return self.handle_no_permission()
                zaak, api_group = result
                self.zaak = zaak
                self.api_group = api_group

        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return TemplateResponse(self.request, "pages/cases/403.html")

        return super().handle_no_permission()


class OuterCaseAccessMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if (
            request.user.is_authenticated
            and not request.user.bsn
            and not request.user.kvk
        ):
            logger.info(
                "OuterCaseAccessMixin - permission denied: user doesn't have a bsn or kvk number"
            )
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
