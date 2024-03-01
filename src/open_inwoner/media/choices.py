from django.db import models
from django.utils.translation import gettext_lazy as _


class VideoPlayerChoices(models.TextChoices):
    vimeo = "vimeo", _("Vimeo")
    youtube = "youtube", _("Youtube")
