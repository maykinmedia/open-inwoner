from django.apps import AppConfig


class MijnUitkeringenCmsConfig(AppConfig):
    name = "open_inwoner.mijn_uitkeringen.cms"
    label = "mijn_uitkeringen_cms"  # Avoid conflict with django-cms
    default_auto_field = "django.db.models.BigAutoField"
