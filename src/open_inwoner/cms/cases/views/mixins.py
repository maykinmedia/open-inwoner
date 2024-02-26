import logging
from typing import Optional

from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _

from open_inwoner.kvk.branches import get_kvk_branch_number
from open_inwoner.openzaak.api_models import Zaak
from open_inwoner.openzaak.clients import build_client
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.types import UniformCase
from open_inwoner.openzaak.utils import is_zaak_visible
from open_inwoner.utils.views import LogMixin

logger = logging.getLogger(__name__)


class CaseLogMixin(LogMixin):
    def log_access_cases(self, cases: list[dict]):
        """
        Log access to cases on the list view

        Creates a single log for all cases
        """
        case_ids = (case["identification"] for case in cases)

        self.log_user_action(
            self.request.user,
            _("Zaken bekeken: {cases}").format(cases=", ".join(case_ids)),
        )

    def log_access_case_detail(self, case: UniformCase):
        self.log_user_action(
            self.request.user,
            _("Zaak bekeken: {case}").format(case=case.identification),
        )


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

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            logger.debug("CaseAccessMixin - permission denied: user not authenticated")
            return self.handle_no_permission()

        if not request.user.bsn and not request.user.kvk:
            logger.debug(
                "CaseAccessMixin - permission denied: user doesn't have a bsn or kvk number"
            )
            return self.handle_no_permission()

        client = build_client("zaak")
        if client is None:
            return super().dispatch(request, *args, **kwargs)

        self.case = self.get_case(client, kwargs)
        if self.case:
            # check if we have a role in this case
            if request.user.bsn:
                if not client.fetch_roles_for_case_and_bsn(
                    self.case.url, request.user.bsn
                ):
                    logger.debug(
                        f"CaseAccessMixin - permission denied: no role for the case {self.case.url}"
                    )
                    return self.handle_no_permission()
            elif request.user.kvk:
                identifier = self.request.user.kvk
                config = OpenZaakConfig.get_solo()
                if config.fetch_eherkenning_zaken_with_rsin:
                    identifier = self.request.user.rsin

                vestigingsnummer = get_kvk_branch_number(self.request.session)
                if (
                    vestigingsnummer
                    and not client.fetch_roles_for_case_and_vestigingsnummer(
                        self.case.url, vestigingsnummer
                    )
                ):
                    logger.debug(
                        f"CaseAccessMixin - permission denied: no role for the case {self.case.url}"
                    )
                    return self.handle_no_permission()

                if not client.fetch_roles_for_case_and_kvk_or_rsin(
                    self.case.url, identifier
                ):
                    logger.debug(
                        f"CaseAccessMixin - permission denied: no role for the case {self.case.url}"
                    )
                    return self.handle_no_permission()

            # resolve case-type
            if catalogi_client := build_client("catalogi"):
                self.case.zaaktype = catalogi_client.fetch_single_case_type(
                    self.case.zaaktype
                )
            else:
                self.case.zaaktype = None

            if not self.case.zaaktype:
                logger.debug(
                    "CaseAccessMixin - permission denied: no case type for case {self.case.url}"
                )
                return self.handle_no_permission()

            # check if case + case-type are visible
            if not is_zaak_visible(self.case):
                logger.debug(
                    "CaseAccessMixin - permission denied: case {self.case.url} is not visible"
                )
                return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return TemplateResponse(self.request, "pages/cases/403.html")

        return super().handle_no_permission()

    def get_case(self, client, kwargs) -> Optional[Zaak]:
        case_uuid = kwargs.get("object_id")
        if not case_uuid:
            return None

        return client.fetch_single_case(case_uuid)


class OuterCaseAccessMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if (
            request.user.is_authenticated
            and not request.user.bsn
            and not request.user.kvk
        ):
            logger.debug(
                "OuterCaseAccessMixin - permission denied: user doesn't have a bsn or kvk number"
            )
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
