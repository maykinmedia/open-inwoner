from django.utils.translation import gettext as _

from djchoices import ChoiceItem, DjangoChoices


class YesNo(DjangoChoices):
    yes = ChoiceItem("yes", _("Ja"))
    no = ChoiceItem("no", _("Nee"))
