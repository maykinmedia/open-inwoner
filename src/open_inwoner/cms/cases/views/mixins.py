import logging
from collections import defaultdict
from typing import List, Optional

from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _

from glom import glom

from open_inwoner.openzaak.api_models import Zaak
from open_inwoner.openzaak.cases import (
    fetch_cases,
    fetch_roles_for_case_and_bsn,
    fetch_single_case,
    fetch_single_status,
)
from open_inwoner.openzaak.catalog import (
    fetch_single_case_type,
    fetch_single_status_type,
)
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.utils import format_zaak_identificatie, is_zaak_visible
from open_inwoner.utils.mixins import PaginationMixin
from open_inwoner.utils.views import LogMixin

logger = logging.getLogger(__name__)


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
            logger.debug("CaseAccessMixin - permission denied: user not authenticated")
            return self.handle_no_permission()

        if not request.user.bsn:
            logger.debug(
                "CaseAccessMixin - permission denied: user doesn't have a bsn "
            )
            return self.handle_no_permission()

        self.case = self.get_case(kwargs)
        if self.case:
            # check if we have a role in this case
            if not fetch_roles_for_case_and_bsn(self.case.url, request.user.bsn):
                logger.debug(
                    f"CaseAccessMixin - permission denied: no role for the case {self.case.url}"
                )
                return self.handle_no_permission()

            # resolve case-type
            self.case.zaaktype = fetch_single_case_type(self.case.zaaktype)
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


class OuterCaseAccessMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.bsn:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
