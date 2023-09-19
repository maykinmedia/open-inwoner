from django.utils.translation import ugettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class VideoPlayerChoices(DjangoChoices):
    vimeo = ChoiceItem("vimeo", _("Vimeo"))
    youtube = ChoiceItem("youtube", _("Youtube"))
