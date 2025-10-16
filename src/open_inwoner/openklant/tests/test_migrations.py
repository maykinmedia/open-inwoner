from django.test import tag

from open_inwoner.utils.tests.test_migrations import TestSuccessfulMigrations


@tag("migrations")
class ContactFormSubjectConfigMigrationTest(TestSuccessfulMigrations):
    migrate_from = "0025_esuiteklantconfig_send_klantcontact_confirmation_email"
    migrate_to = "0026_contactform_subject_config_default"
    app = "openklant"

    def setUpBeforeMigration(self, apps):
        ContactFormSubject = apps.get_model("openklant", "ContactFormSubject")
        ESuiteKlantConfig = apps.get_model("openklant", "ESuiteKlantConfig")
        OpenKlant2Config = apps.get_model("openklant", "OpenKlant2Config")

        self.esuite_config_1 = ESuiteKlantConfig.objects.create()
        self.esuite_config_2 = ESuiteKlantConfig.objects.create()
        self.openklant_config_1 = OpenKlant2Config.objects.create()
        self.openklant_config_2 = OpenKlant2Config.objects.create()

        for contact_form_subject in ContactFormSubject.objects.all():
            contact_form_subject.esuite_config = None
            contact_form_subject.openklant_config = None
            contact_form_subject.save()

    def test_set_default_config(self):
        ContactFormSubject = self.apps.get_model("openklant", "ContactFormSubject")

        for contact_form_subject in ContactFormSubject.objects.all():
            self.assertEqual(contact_form_subject.esuite_config, self.esuite_config_1)
            self.assertEqual(
                contact_form_subject.openklant_config, self.openklant_config_1
            )


@tag("migrations")
class ContactFormtConfigMigrationTest(TestSuccessfulMigrations):
    migrate_from = "0027_alter_klantensysteemconfig_primary_backend"
    migrate_to = "0028_change_contactformconfig_descriptions"
    app = "openklant"

    def setUpBeforeMigration(self, apps):
        ContactFormConfig = apps.get_model("openklant", "ContactFormConfig")
        Placeholder = apps.get_model("cms", "Placeholder")

        # Create a placeholder for the CMS plugin
        placeholder = Placeholder.objects.create(slot="test")

        # Create the ContactFormConfig plugin instance with required MPTT fields
        self.config = ContactFormConfig.objects.create(
            placeholder=placeholder,
            position=0,
            language="nl",
            plugin_type="ContactFormPlugin",
            description="Old contactform description",
            # required by CMSPlugin for tree traversal
            depth=1,
            path="0001",
            numchild=0,
        )

    def test_migrate_contactform_description(self):
        ContactFormConfig = self.apps.get_model("openklant", "ContactFormConfig")

        for config in ContactFormConfig.objects.all():
            self.assertEqual(
                config.description_authenticated_user, "Old contactform description"
            )
            self.assertEqual(
                config.description_anonymous_user, "Old contactform description"
            )
