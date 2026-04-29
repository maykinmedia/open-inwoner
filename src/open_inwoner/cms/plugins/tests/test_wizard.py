from django.test import TestCase, override_settings

from cms.forms.wizards import CreateCMSPageForm
from cms.wizards.forms import WizardStep2BaseForm, step2_form_factory

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.plugins.models import Text

CreateCMSPageForm = step2_form_factory(
    mixin_cls=WizardStep2BaseForm,
    entry_form_class=CreateCMSPageForm,
)


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class CMSPageWizardTextPluginTest(TestCase):
    """
    Tests that the CMS page creation wizard does not corrupt Prosemirror body
    fields. CMS_PAGE_WIZARD_CONTENT_PLUGIN_BODY = "" disables the wizard's
    plain-text content pre-fill, preventing raw strings from reaching the body column.
    """

    def setUp(self):
        self.superuser = UserFactory.create(is_superuser=True, is_staff=True)

    def _make_form(self, content="some content"):
        return CreateCMSPageForm(
            data={
                "title": "Test page",
                "slug": "test-page",
                "page_type": None,
                "content": content,
            },
            wizard_page=None,
            wizard_user=self.superuser,
            wizard_language="nl",
        )

    def test_wizard_does_not_create_text_plugin_with_plain_string_body(self):
        """With CMS_PAGE_WIZARD_CONTENT_PLUGIN_BODY = "" no Text plugin is created."""
        form = self._make_form()
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        self.assertEqual(
            Text.objects.count(),
            0,
            "Wizard must not create a Text plugin when CONTENT_PLUGIN_BODY is disabled.",
        )
