import logging

from open_inwoner.openklant.clients import build_klanten_client
from open_inwoner.openklant.wrap import get_fetch_parameters

logger = logging.getLogger(__name__)


class KlantenAPIMixin:
    def patch_klant(self, update_data: dict):
        if update_data and (client := build_klanten_client()):
            klant = client.retrieve_klant(**get_fetch_parameters(self.request))
            if not klant:
                logger.error("Failed to retrieve klant for user %s", self.request.user)
                return

            self.log_system_action("retrieved klant for user", user=self.request.user)
            client.partial_update_klant(klant, update_data)
            self.log_system_action(
                f"patched klant from user profile edit with fields: {', '.join(sorted(update_data.keys()))}",
                user=self.request.user,
            )
