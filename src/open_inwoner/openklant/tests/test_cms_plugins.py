from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.tests import cms_tools
from open_inwoner.openklant.cms_plugins import ContactFormPlugin
from open_inwoner.openklant.forms import ContactForm


class ContactFormPluginRenderTest(TestCase):
    """Unit tests for `ContactForm` CMS plugin"""

    def test_contact_form_plugin_authenticated_user(self):
        description_authenticated_user = (
            "A description for the contactform (authenticated users)"
        )
        description_anonymous_user = (
            "A description for the contactform (anonymous users)"
        )

        user = UserFactory()
        form = ContactForm(user=user, request_session={})

        html, context = cms_tools.render_plugin(
            ContactFormPlugin,
            plugin_data={
                "description_authenticated_user": description_authenticated_user,
                "description_anonymous_user": description_anonymous_user,
            },
            user=user,
            request_context={
                "form": form,
                "has_form_configuration": True,
            },
        )

        self.assertIn(
            f'<p class="utrecht-paragraph">{description_authenticated_user}</p>', html
        )
        self.assertNotIn(
            f'<p class="utrecht-paragraph">{description_anonymous_user}</p>', html
        )

    def test_contact_form_plugin_anonymous_user(self):
        description_authenticated_user = (
            "A description for the contactform (authenticated users)"
        )
        description_anonymous_user = (
            "A description for the contactform (anonymous users)"
        )

        user = UserFactory()
        form = ContactForm(user=user, request_session={})

        html, context = cms_tools.render_plugin(
            ContactFormPlugin,
            plugin_data={
                "description_authenticated_user": description_authenticated_user,
                "description_anonymous_user": description_anonymous_user,
            },
            user=AnonymousUser(),
            request_context={
                "form": form,
                "has_form_configuration": True,
            },
        )

        self.assertNotIn(
            f'<p class="utrecht-paragraph">{description_authenticated_user}</p>', html
        )
        self.assertIn(
            f'<p class="utrecht-paragraph">{description_anonymous_user}</p>', html
        )
