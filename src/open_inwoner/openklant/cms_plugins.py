from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _

from cms.models import CMSPlugin
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from open_inwoner.ckeditor5.widgets import CKEditorWidget


class ContactFormConfig(CMSPlugin):
    description_authenticated_user = models.TextField(
        _("Description authenticated users"),
        blank=True,
        help_text=_("Description of the contact form for authenticated users"),
    )
    description_anonymous_user = models.TextField(
        _("Description anonymous users"),
        blank=True,
        help_text=_(
            "Description of the contact form for anonymous/non-authenticated users"
        ),
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
    app_hook = "OpenKlantApphook"
    name = _("Contact form plugin")
    render_template = "cms/contactform/form_inner.html"
    cache = False

    def render(self, context, instance, placeholder):
        user = context["request"].user
        form_description = (
            instance.description_authenticated_user
            if user.is_authenticated
            else instance.description_anonymous_user
        )
        context.update(
            {
                "plugin_instance": instance,
                "form_description": form_description,
            }
        )
        return context
