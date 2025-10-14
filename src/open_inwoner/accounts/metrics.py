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
    name="user_count",
    description="The number of application users in the database.",
    unit="",  # no unit so that the _ratio suffix is not added
    callbacks=[count_users],
)

logins = meter.create_counter(
    "auth.logins",
    unit="1",  # unitless count
    description="The number of successful user logins.",
)

logouts = meter.create_counter(
    "auth.logouts",
    unit="1",  # unitless count
    description="The number of user logouts.",
)

login_failures = meter.create_counter(
    "auth.login_failures",
    unit="1",  # unitless count
    description="The number of failed logins by users, including the admin.",
)

user_lockouts = meter.create_counter(
    "auth.user_lockouts",
    unit="1",  # unitless count
    description="The number of user lockouts because of failed logins.",
)

contactmoment_list_views = meter.create_counter(
    "contactmoments.list_views",
    unit="1",
    description=(
        "Number of times users view the contactmoments list. "
        "Attributes: num_questions_viewed (int)"
    ),
)

contactmoment_detail_views = meter.create_counter(
    "contactmoments.detail_views",
    unit="1",
    description="Number of times users view contactmoment details",
)

contactmoment_registrations = meter.create_counter(
    "contactmoments.registrations",
    unit="1",
    description=(
        "Contactmoment/question registrations. "
        "Attributes: channel ('email', 'esuite', or 'openklant'), success (bool)"
    ),
)

profile_updates = meter.create_counter(
    "profile.updates",
    unit="1",
    description="Number of times users update their profile information",
)

profile_update_failures = meter.create_counter(
    "profile.update_failures",
    unit="1",
    description=(
        "Profile update failures due to API service issues. "
        "Attributes: failed_services (str), changed_fields (str)"
    ),
)

profile_categories_updates = meter.create_counter(
    "profile.categories_updates",
    unit="1",
    description="Number of times users update their interest categories",
)

profile_newsletter_updates = meter.create_counter(
    "profile.newsletter_updates",
    unit="1",
    description="Number of times users update newsletter subscriptions. Attributes: success (bool)",
)

profile_notifications_updates = meter.create_counter(
    "profile.notifications_updates",
    unit="1",
    description="Number of times users update their notification preferences",
)

profile_deletions = meter.create_counter(
    "profile.deletions",
    unit="1",
    description="Number of times users delete their account via the frontend",
)

brp_data_requests = meter.create_counter(
    "profile.brp_data_requests",
    unit="1",
    description="Number of times users request their BRP (personal) data",
)

invites_accepted = meter.create_counter(
    "registration.invites_accepted",
    unit="1",
    description="Number of invites accepted",
)

necessary_fields_completions = meter.create_counter(
    "registration.necessary_fields_completions",
    unit="1",
    description=(
        "Number of times users complete necessary registration fields. "
        "Attributes: has_invite (bool), updated_esuite (bool), updated_openklant (bool)"
    ),
)

email_verification_requests = meter.create_counter(
    "registration.email_verification_requests",
    unit="1",
    description="Number of email verification requests by users",
)

email_verification_completions = meter.create_counter(
    "registration.email_verification_completions",
    unit="1",
    description="Number of email verification completions. Attributes: success (bool)",
)
