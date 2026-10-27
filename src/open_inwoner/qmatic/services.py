import requests
import structlog

from open_inwoner.accounts.models import User

from .client import Appointment, NoServiceConfigured, qmatic_client_factory
from .exceptions import QmaticException

logger = structlog.stdlib.get_logger(__name__)


def get_appointments_for_user(user: User) -> list[Appointment]:
    """
    Return the user's upcoming Qmatic appointments.

    Appointments are looked up by verified email, so a user without one gets
    none. Qmatic not being configured or failing to respond is logged and also
    results in no appointments, so the pages showing them keep working.
    """
    if not user.has_verified_email():
        return []

    try:
        client = qmatic_client_factory()
    except NoServiceConfigured:
        logger.warning("Error occurred while creating Qmatic client")
        return []

    try:
        return client.list_appointments_for_customer(user.verified_email)
    except (QmaticException, requests.RequestException):
        logger.exception("Error occurred while retrieving Qmatic appointments")
        return []
