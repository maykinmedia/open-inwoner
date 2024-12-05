from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _

from cms.models import CMSPlugin
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from open_inwoner.ckeditor5.widgets import CKEditorWidget
from open_inwoner.openklant.forms import ContactForm
from open_inwoner.openklant.models import OpenKlantConfig

#
# contact form plugin
#


class ContactFormConfig(CMSPlugin):
    title = models.TextField(
        _("Title"),
        blank=True,
        help_text=_("Title of the contact form."),
    )
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
            "title": CKEditorWidget,
            "description": CKEditorWidget,
        }


@plugin_pool.register_plugin
class ContactFormPlugin(CMSPluginBase):
    model = ContactFormConfig
    form = ContactFormConfigForm
    name = _("Contact form plugin")
    render_template = "pages/contactform/form.html"
    # render_template = "cms/contactform/form.html"
    cache = False

    fieldsets = ((None, {"fields": ("title", "description")}),)

    def render(self, context, instance, placeholder):
        config = OpenKlantConfig.get_solo()
        context.update(
            {
                "has_form_configuration": config.has_form_configuration(),
                "form": ContactForm(
                    user=context["user"], request_session=context["request"].session
                ),
                "instance": instance,
                "title": instance.title,
                "description": instance.description,
            }
        )
        return context
