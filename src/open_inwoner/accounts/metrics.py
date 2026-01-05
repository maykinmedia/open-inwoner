from collections.abc import Collection

from django.db.models import Count, Q

from opentelemetry import metrics

from .choices import LoginTypeChoices
from .models import User

meter = metrics.get_meter("open_inwoner.accounts")


def count_users(options: metrics.CallbackOptions) -> Collection[metrics.Observation]:
    counts: dict[str, int] = User.objects.aggregate(
        total=Count("id"),
        staff=Count("id", filter=Q(is_staff=True)),
        superuser=Count("id", filter=Q(is_superuser=True)),
        login_default=Count("id", filter=Q(login_type=LoginTypeChoices.default)),
        login_digid=Count("id", filter=Q(login_type=LoginTypeChoices.digid)),
        login_eherkenning=Count(
            "id", filter=Q(login_type=LoginTypeChoices.eherkenning)
        ),
        login_oidc=Count("id", filter=Q(login_type=LoginTypeChoices.oidc)),
    )
    return (
        metrics.Observation(
            counts["total"],
            {"scope": "global", "type": "all"},
        ),
        metrics.Observation(
            counts["staff"],
            {"scope": "global", "type": "staff"},
        ),
        metrics.Observation(
            counts["superuser"],
            {"scope": "global", "type": "superuser"},
        ),
        metrics.Observation(
            counts["login_default"],
            {"scope": "global", "type": "all", "login_type": "default"},
        ),
        metrics.Observation(
            counts["login_digid"],
            {"scope": "global", "type": "all", "login_type": "digid"},
        ),
        metrics.Observation(
            counts["login_eherkenning"],
            {"scope": "global", "type": "all", "login_type": "eherkenning"},
        ),
        metrics.Observation(
            counts["login_oidc"],
            {"scope": "global", "type": "all", "login_type": "oidc"},
        ),
    )


meter.create_observable_gauge(
    name="oip.accounts.user_count",
    description="The number of application users in the database.",
    unit="",  # no unit so that the _ratio suffix is not added
    callbacks=[count_users],
)

logins = meter.create_counter(
    "oip.auth.logins",
    unit="{login}",
    description="The number of successful user logins.",
)

logouts = meter.create_counter(
    "oip.auth.logouts",
    unit="{logout}",
    description="The number of user logouts.",
)

login_failures = meter.create_counter(
    "oip.auth.login_failures",
    unit="{failure}",
    description="The number of failed logins by users, including the admin.",
)

user_lockouts = meter.create_counter(
    "oip.auth.user_lockouts",
    unit="{lockout}",
    description="The number of user lockouts because of failed logins.",
)

contactmoment_list_views = meter.create_counter(
    "oip.contactmoments.list_views",
    unit="{view}",
    description=(
        "Number of times users view the contactmoments list. "
        "Attributes: num_questions_viewed (int)"
    ),
)

contactmoment_detail_views = meter.create_counter(
    "oip.contactmoments.detail_views",
    unit="{view}",
    description="Number of times users view contactmoment details",
)

contactmoment_registrations = meter.create_counter(
    "oip.contactmoments.registrations",
    unit="{registration}",
    description=(
        "Contactmoment/question registrations. "
        "Attributes: channel ('email', 'esuite', or 'openklant'), success (bool)"
    ),
)

profile_updates = meter.create_counter(
    "oip.accounts.profile_updates",
    unit="{update}",
    description="Number of times users update their profile information",
)

profile_update_failures = meter.create_counter(
    "oip.profile.update_failures",
    unit="{failure}",
    description=(
        "Profile update failures due to API service issues. "
        "Attributes: failed_services (str), changed_fields (str)"
    ),
)

profile_categories_updates = meter.create_counter(
    "oip.profile.categories_updates",
    unit="{update}",
    description="Number of times users update their interest categories",
)

profile_newsletter_updates = meter.create_counter(
    "oip.profile.newsletter_updates",
    unit="{update}",
    description="Number of times users update newsletter subscriptions. Attributes: success (bool)",
)

profile_notifications_updates = meter.create_counter(
    "oip.profile.notifications_updates",
    unit="{update}",
    description="Number of times users update their notification preferences",
)

profile_deletions = meter.create_counter(
    "oip.profile.deletions",
    unit="{deletion}",
    description="Number of times users delete their account via the frontend",
)

brp_data_requests = meter.create_counter(
    "oip.profile.brp_data_requests",
    unit="{request}",
    description="Number of times users request their BRP (personal) data",
)

invites_accepted = meter.create_counter(
    "oip.registration.invites_accepted",
    unit="{invite}",
    description="Number of invites accepted",
)

necessary_fields_completions = meter.create_counter(
    "oip.registration.necessary_fields_completions",
    unit="{completion}",
    description=(
        "Number of times users complete necessary registration fields. "
        "Attributes: has_invite (bool), updated_esuite (bool), updated_openklant (bool)"
    ),
)

email_verification_requests = meter.create_counter(
    "oip.registration.email_verification_requests",
    unit="{request}",
    description="Number of email verification requests by users",
)

email_verification_completions = meter.create_counter(
    "oip.registration.email_verification_completions",
    unit="{completion}",
    description="Number of email verification completions. Attributes: success (bool)",
)
