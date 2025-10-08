from functools import partial

from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from open_inwoner.accounts.metrics import (
    contactmoment_detail_views,
    contactmoment_list_views,
    contactmoment_registrations,
)
from open_inwoner.accounts.models import User
from open_inwoner.utils.logentry import system_error
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

        contactmoment_registrations.add(1, {"channel": "email", "success": success})

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

        contactmoment_registrations.add(1, {"channel": "openklant", "success": success})

    def log_contactmoment_registered_via_esuite(self, success: bool):
        """
        Log registering a contactmoment via eSuite
        """
        log = partial(self.log_system_action, user=self.request.user)

        if success:
            log("registered contactmoment via eSuite")
        else:
            log("error while registering contactmoment by API")

        contactmoment_registrations.add(1, {"channel": "esuite", "success": success})

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

    def log_contactmoment_list_accessed(self, questions: list[dict]):
        """
        Log access to the contactmoment list view

        Creates a single log for all questions
        """
        question_ids = (question["identification"] for question in questions)

        self.log_user_action(
            self.request.user,
            f"Vragen bekeken: {', '.join(question_ids)}",
        )
        contactmoment_list_views.add(1, {"num_questions_viewed": len(questions)})

    def log_contactmoment_detail_accessed(self, identification: str):
        """
        Log access to a specific contactmoment detail view
        """
        self.log_user_action(
            self.request.user,
            f"Vraag bekeken: {identification}",
        )
        contactmoment_detail_views.add(1)


class ProfileLogMixin(LogMixin):
    request: HttpRequest

    def log_newsletter_subscription_modified(self, success: bool):
        if success:
            self.log_user_action(
                self.request.user, _("users newsletter subscriptions were modified")
            )
        else:
            self.log_user_action(
                self.request.user, _("failed to modify user newsletter subscription")
            )

    def log_user_deleted(self, user: User):
        self.log_user_action(user, _("user was deleted via frontend"))

    def log_profile_modified(self, user: User):
        self.log_change(user, _("profile was modified"))

    def log_profile_update_failed(
        self, user: User, failed_services: list[str], changed_fields: list[str]
    ):
        log_msg = (
            "API service failure when updating user profile. "
            "Failed services: %(failed_services)s. "
            "Changed fields: %(changed_fields)s"
            % {
                "failed_services": " and ".join(failed_services),
                "changed_fields": ", ".join(changed_fields),
            }
        )
        system_error(message=log_msg, user=user)

    def log_digitaal_adres_deleted(self, user: User, digitaal_adres_uuid: str):
        self.log_system_action(
            f"deleted old digitaal adres {digitaal_adres_uuid}",
            instance=user,
        )

    def log_categories_modified(self, user: User):
        self.log_change(user, _("categories were modified"))

    def log_brp_data_requested(self):
        self.log_user_action(self.request.user, _("user requests for brp data"))

    def log_notifications_modified(self, user: User):
        self.log_change(user, _("users notifications were modified"))
