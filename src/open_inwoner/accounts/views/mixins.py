import logging

from open_inwoner.openklant.models import OpenKlantConfig
from open_inwoner.openklant.services import eSuiteKlantenService

logger = logging.getLogger(__name__)


class KlantenAPIMixin:
    def patch_klant(self, update_data: dict):
        if not update_data:
            return

        try:
            service = eSuiteKlantenService(config=OpenKlantConfig.get_solo())
        except RuntimeError:
            logger.error("Error building KlantenService")
            return

        klant = service.retrieve_klant(**service.get_fetch_parameters(self.request))
        if not klant:
            logger.error("Failed to retrieve klant for user %s", self.request.user)
            return

        self.log_system_action("retrieved klant for user", user=self.request.user)
        service.partial_update_klant(klant, update_data)
        self.log_system_action(
            f"patched klant from user profile edit with fields: {', '.join(sorted(update_data.keys()))}",
            user=self.request.user,
        )
