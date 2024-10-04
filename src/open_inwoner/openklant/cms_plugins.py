from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _

from cms.models import CMSPlugin
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from open_inwoner.ckeditor5.widgets import CKEditorWidget

#
# contact form plugin
#


class ContactFormConfig(CMSPlugin):
    description = models.TextField(
        _("Description"),
        blank=True,
        help_text=_("Description of the contact form."),
    )


class ContactFormConfigForm(forms.ModelForm):
    class Meta:
        model = ContactFormConfig
        fields = "__all__"
        widgets = {
            "description": CKEditorWidget,
        }


@plugin_pool.register_plugin
class ContactFormPlugin(CMSPluginBase):
    model = ContactFormConfig
    form = ContactFormConfigForm
    name = _("Contact form plugin")
    render_template = "pages/contactform/form.html"
    cache = False
