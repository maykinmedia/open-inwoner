from django.test import tag

from open_inwoner.questionnaire.tests.factories import QuestionnaireStepFactory
from open_inwoner.utils.tests.test_migrations import TestSuccessfulMigrations


def _text_with_link(text, href):
    return {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": text,
                        "marks": [{"type": "link", "attrs": {"href": href}}],
                    }
                ],
            }
        ],
    }


@tag("migrations")
class SanitizeProsemirrorLinkHrefsMigrationTest(TestSuccessfulMigrations):
    """
    Test migration 0027: strip unsafe hrefs from stored prosemirror link marks
    on QuestionnaireStep.content.
    """

    migrate_from = "0026_alter_questionnairestep_content"
    migrate_to = "0027_sanitize_prosemirror_link_hrefs"
    app = "questionnaire"

    def setUpBeforeMigration(self, apps):
        QuestionnaireStep = apps.get_model("questionnaire", "QuestionnaireStep")

        real_step = QuestionnaireStepFactory()
        self.step = QuestionnaireStep.objects.get(id=real_step.id)
        QuestionnaireStep.objects.filter(pk=self.step.pk).update(
            content=_text_with_link("click", "javascript:alert(document.cookie)")
        )

        real_safe_step = QuestionnaireStepFactory(path="0002")
        self.safe_step = QuestionnaireStep.objects.get(id=real_safe_step.id)
        QuestionnaireStep.objects.filter(pk=self.safe_step.pk).update(
            content=_text_with_link("click", "#anchor")
        )

    def _get(self, step):
        QuestionnaireStep = self.apps.get_model("questionnaire", "QuestionnaireStep")
        return QuestionnaireStep.objects.get(id=step.id)

    def test_unsafe_href_stripped_from_content(self):
        step = self._get(self.step)
        text_node = step.content.raw_data["content"][0]["content"][0]
        self.assertEqual(text_node["marks"], [])

    def test_safe_href_preserved_on_content(self):
        step = self._get(self.safe_step)
        text_node = step.content.raw_data["content"][0]["content"][0]
        self.assertEqual(text_node["marks"][0]["attrs"]["href"], "#anchor")
