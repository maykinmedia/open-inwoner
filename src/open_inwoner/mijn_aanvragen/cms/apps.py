from django.apps import AppConfig


class MijnAanvragenCmsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "open_inwoner.mijn_aanvragen.cms"
    label = "openzaak_cms"  # Keep the old label to avoid migrations
