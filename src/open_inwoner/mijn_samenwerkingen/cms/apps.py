from django.apps import AppConfig


class MijnSamenwerkingenCmsConfig(AppConfig):
    name = "open_inwoner.mijn_samenwerkingen.cms"
    label = "mijn_samenwerkingen_cms"  # Avoid conflict with django-cms
    default_auto_field = "django.db.models.BigAutoField"
