from django.test import TestCase

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.tests import cms_tools
from open_inwoner.openklant.cms_plugins import ContactFormPlugin
from open_inwoner.openklant.forms import ContactForm


class ContactFormPluginRenderTest(TestCase):
    """Unit tests for `ContactForm` CMS plugin"""

    def test_contact_form_plugin_render(self):
        description = "A description for the contactform"

        user = UserFactory()
        form = ContactForm(user=user, request_session={})

        html, context = cms_tools.render_plugin(
            ContactFormPlugin,
            plugin_data={"description": description},
            user=user,
            request_context={
                "form": form,
                "has_form_configuration": True,
            },
        )

        self.assertIn(f'<p class="utrecht-paragraph">{description}</p>', html)
