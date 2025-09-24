from open_inwoner.utils.tests.test_migrations import TestSuccessfulMigrations


class QuestionnaireStepContentMigrationTest(TestSuccessfulMigrations):
    migrate_from = "0021_alter_questionnairestep_category"
    migrate_to = "0024_questionnairestep_content_schema_2"
    app = "questionnaire"

    def setUpBeforeMigration(self, apps):
        QuestionnaireStep = apps.get_model("questionnaire", "QuestionnaireStep")

        questionnaire_step = QuestionnaireStep.objects.create(
            # Required fields for the model
            code="test-code",
            slug="test-slug",
            question="Test Question",
            question_subject="Test",
            # Required treebeard fields
            path="0001",
            depth=1,
            numchild=0,
            # Field being migrated
            content='<p>This is a <strong>test</strong> text with <em>formatting</em> and a <a href="https://example.com">link</a>.</p>',
        )
        test_html = '<p>This is a <strong>test</strong> text with <em>formatting</em> and a <a href="https://example.com">link</a>.</p>'
        questionnaire_step.content = test_html
        questionnaire_step.save()

    def test_questionnaire_step_content(self):
        QuestionnaireStep = self.apps.get_model("questionnaire", "QuestionnaireStep")

        questionnaire_step = QuestionnaireStep.objects.first()

        expected_content = '<p>This is a <strong>test</strong> text with <em>formatting</em> and a <a href="https://example.com">link</a>.</p>'
        self.assertEqual(questionnaire_step.content.html, expected_content)

        # Verify that the temporary field was removed
        self.assertFalse(hasattr(questionnaire_step, "warning_banner_text_tmp"))
