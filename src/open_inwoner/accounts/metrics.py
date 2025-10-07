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
