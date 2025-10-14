from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from open_inwoner.accounts.metrics import (
    brp_data_requests,
    contactmoment_detail_views,
    contactmoment_list_views,
    contactmoment_registrations,
    email_verification_completions,
    email_verification_requests,
    invites_accepted,
    necessary_fields_completions,
    profile_categories_updates,
    profile_deletions,
    profile_newsletter_updates,
    profile_notifications_updates,
    profile_update_failures,
    profile_updates,
)
from open_inwoner.accounts.models import User
from open_inwoner.utils.logentry import system_error
from open_inwoner.utils.views import LogMixin


class ContactmomentLogMixin(LogMixin):
    request: HttpRequest

    def log_contactmoment_registered_by_email(self, success: bool):
        if success:
            msg = "registered contactmoment by email"
        else:
            msg = "error while registering contactmoment by email"

        self.log_system_action(msg, user=self.request.user)
        contactmoment_registrations.add(1, {"channel": "email", "success": success})

    def log_question_registered_via_openklant(self, success: bool):
        if success:
            msg = "registered question via OpenKlant"
        else:
            msg = "failed to register question via OpenKlant"

        self.log_system_action(msg, user=self.request.user)
        contactmoment_registrations.add(1, {"channel": "openklant", "success": success})

    def log_contactmoment_registered_via_esuite(self, success: bool):
        if success:
            msg = "registered contactmoment via eSuite"
        else:
            msg = "error while registering contactmoment by API"

        self.log_system_action(msg, user=self.request.user)
        contactmoment_registrations.add(1, {"channel": "esuite", "success": success})

    def log_klant_patched(self, patched_fields: list[str]):
        self.log_system_action(
            "patched klant from user with missing fields: {patched}".format(
                patched=", ".join(sorted(patched_fields))
            ),
            user=self.request.user,
        )

    def log_klant_contact_info_appended_to_message(self):
        self.log_system_action(
            "could not retrieve or create klant for user, appended info to message",
            user=self.request.user,
        )

    def log_contactmoment_list_accessed(self, questions: list[dict]):
        question_ids = (question["identification"] for question in questions)

        self.log_user_action(
            self.request.user,
            f"Vragen bekeken: {', '.join(question_ids)}",
        )
        contactmoment_list_views.add(1, {"num_questions_viewed": len(questions)})

    def log_contactmoment_detail_accessed(self, identification: str):
        self.log_user_action(
            self.request.user,
            f"Vraag bekeken: {identification}",
        )
        contactmoment_detail_views.add(1)


class ProfileLogMixin(LogMixin):
    request: HttpRequest

    def log_newsletter_subscription_modified(self, success: bool):
        if success:
            msg = _("users newsletter subscriptions were modified")
        else:
            msg = _("failed to modify user newsletter subscription")

        self.log_user_action(self.request.user, msg)
        profile_newsletter_updates.add(1, {"success": success})

    def log_user_deleted(self, user: User):
        self.log_user_action(user, _("user was deleted via frontend"))
        profile_deletions.add(1)

    def log_profile_modified(self, user: User):
        self.log_change(user, _("profile was modified"))
        profile_updates.add(1)

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
        profile_update_failures.add(
            1,
            {
                "failed_services": " and ".join(failed_services),
                "changed_fields": ", ".join(changed_fields),
            },
        )

    def log_digitaal_adres_deleted(self, user: User, digitaal_adres_uuid: str):
        self.log_system_action(
            f"deleted old digitaal adres {digitaal_adres_uuid}",
            instance=user,
        )

    def log_categories_modified(self, user: User):
        self.log_change(user, _("categories were modified"))
        profile_categories_updates.add(1)

    def log_brp_data_requested(self):
        self.log_user_action(self.request.user, _("user requests for brp data"))
        brp_data_requests.add(1)

    def log_notifications_modified(self, user: User):
        self.log_change(user, _("users notifications were modified"))
        profile_notifications_updates.add(1)


class RegistrationLogMixin(LogMixin):
    request: HttpRequest

    def log_invite_accepted(self):
        invites_accepted.add(1)

    def log_necessary_fields_completed(
        self,
        user: User,
        has_invite: bool,
        updated_esuite: bool,
        updated_openklant: bool,
    ):
        self.log_user_action(user, _("user was updated with necessary fields"))
        necessary_fields_completions.add(
            1,
            {
                "has_invite": has_invite,
                "updated_esuite": updated_esuite,
                "updated_openklant": updated_openklant,
            },
        )

    def log_custom_user_registration(self, user):
        self.log_user_action(user, _("user was created"))

    def log_email_verification_requested(self, user: User):
        self.log_user_action(user, _("user requested e-mail address verification"))
        email_verification_requests.add(1)

    def log_email_verification_completed(self, user: User, success: bool):
        if success:
            msg = _("user verified e-mail address")
        else:
            msg = _("user failed to verify e-mail address")

        self.log_user_action(user, msg)
        email_verification_completions.add(1, {"success": success})
