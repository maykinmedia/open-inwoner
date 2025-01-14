import logging

from django.core.exceptions import ImproperlyConfigured

from open_inwoner.openklant.models import ESuiteKlantConfig
from open_inwoner.openklant.services import eSuiteKlantenService

logger = logging.getLogger(__name__)


class KlantenAPIMixin:
    def patch_klant(self, update_data: dict):
        if not update_data:
            return

        try:
            service = eSuiteKlantenService(config=ESuiteKlantConfig.get_solo())
        except ImproperlyConfigured:
            logger.error("Error building KlantenService")
            return

        klant, klant_created = service.get_or_create_klant(
            fetch_params=service.get_fetch_parameters(self.request),
            user=self.request.user,
        )
        if not klant:
            logger.error("Failed to retrieve klant for user %s", self.request.user)
            return

        if klant_created:
            self.log_system_action("created klant for user", user=self.request.user)
        else:
            self.log_system_action("retrieved klant for user", user=self.request.user)

        service.partial_update_klant(klant, update_data)
        self.log_system_action(
            f"patched klant from user profile edit with fields: {', '.join(sorted(update_data.keys()))}",
            user=self.request.user,
        )
