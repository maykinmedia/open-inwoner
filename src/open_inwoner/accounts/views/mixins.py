from functools import partial

from django.http import HttpRequest

from open_inwoner.utils.views import LogMixin


class ContactmomentLogMixin(LogMixin):
    request: HttpRequest

    def log_contactmoment_registered_by_email(self, success: bool):
        """
        Log registering a contactmoment by email
        """
        log = partial(self.log_system_action, user=self.request.user)

        if success:
            log("registered contactmoment by email")
        else:
            log("error while registering contactmoment by email")

    def log_question_registered_via_openklant(self, success: bool):
        """
        Log registering a question via OpenKlant2
        """
        if success:
            self.log_system_action(
                "registered question via OpenKlant", user=self.request.user
            )
        else:
            self.log_system_action("failed to register question via OpenKlant")

    def log_contactmoment_registered_via_esuite(self, success: bool):
        """
        Log registering a contactmoment via eSuite
        """
        log = partial(self.log_system_action, user=self.request.user)

        if success:
            log("registered contactmoment via eSuite")
        else:
            log("error while registering contactmoment by API")

    def log_klant_patched(self, patched_fields: list[str]):
        """
        Log patching a klant with missing fields
        """
        self.log_system_action(
            "patched klant from user with missing fields: {patched}".format(
                patched=", ".join(sorted(patched_fields))
            ),
            user=self.request.user,
        )

    def log_klant_contact_info_appended_to_message(self):
        """
        Log when contact info is appended to message because klant couldn't be created
        """
        self.log_system_action(
            "could not retrieve or create klant for user, appended info to message",
            user=self.request.user,
        )
