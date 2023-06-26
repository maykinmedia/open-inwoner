from django.utils.translation import ugettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class ColorTypeChoices(DjangoChoices):
    light = ChoiceItem("#FFFFFF", _("light"))
    dark = ChoiceItem("#4B4B4B", _("dark"))


class OpenIDDisplayChoices(DjangoChoices):
    admin = ChoiceItem("admin", _("Admin"))
    regular = ChoiceItem("regular", _("Regular user"))
