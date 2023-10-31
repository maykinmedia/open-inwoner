import logging

from open_inwoner.openzaak.cases import fetch_roles_for_case_and_bsn

logger = logging.getLogger(__name__)


def check_user_auth(user, digid_required: bool = False) -> bool:
    if not user.is_authenticated:
        logger.debug("Permission denied: user not authenticated")
        return False
    if digid_required and not getattr(user, "bsn", None):
        logger.debug("Permission denied: user has no BSN")
        return False
    return True


def check_user_access_rights(user, case_url) -> bool:
    if not fetch_roles_for_case_and_bsn(case_url, user.bsn):
        logger.debug(f"Permission denied: no role for the case {case_url}")
        return False
    return True
