from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site

import structlog

logger = structlog.stdlib.get_logger(__name__)


def get_or_create_migration_user(user_model=get_user_model()):
    """
    :return: Object: User, Bool: if the user was created

    This is the user that is used to automatically attach to new items created as
    part of the cms migration.
    """
    if getattr(settings, "CMS_MIGRATION_USER_ID", None):
        return user_model.objects.get(id=settings.CMS_MIGRATION_USER_ID), False

    # Get the USERNAME_FIELD from the *real* user model, not the potentially
    # historical model passed in — historical models from apps.get_model() don't
    # carry custom class attributes like USERNAME_FIELD and fall back to Django's
    # default "username", causing "Cannot resolve keyword 'username'" errors.
    username_field = get_user_model().USERNAME_FIELD

    # Determine appropriate value based on field type
    if username_field == "email":
        username_value = "djangocms_4_migration_user@example.com"
    else:
        username_value = "djangocms_4_migration_user"

    return user_model.objects.get_or_create(
        **{
            username_field: username_value,
            "is_staff": True,
            "is_superuser": True,
        }
    )


def get_default_site():
    site_id = getattr(settings, "MIGRATION_DEFAULT_SITE_ID", None) or getattr(
        settings, "SITE_ID", 1
    )
    return (
        Site.objects.filter(id=site_id).first() or Site.objects.order_by("id").first()
    )
