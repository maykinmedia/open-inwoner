from django.utils.translation import gettext_lazy as _

from cms.models import CMSPlugin
from django_prosemirror.fields import ProsemirrorModelField


class Text(CMSPlugin):
    body = ProsemirrorModelField(
        _("Body"),
        help_text=_("The text content"),
    )

    def __str__(self):
        return self.body.html
