from open_inwoner.utils.tests.test_migrations import TestSuccessfulMigrations


class ContactFormSubjectConfigMigrationTest(TestSuccessfulMigrations):
    migrate_from = "0025_esuiteklantconfig_send_klantcontact_confirmation_email"
    migrate_to = "0026_contactform_subject_config_default"
    app = "openklant"

    def setUpBeforeMigration(self, app):
        ContactFormSubject = app.get_model("openklant", "ContactFormSubject")
        ESuiteKlantConfig = app.get_model("openklant", "ESuiteKlantConfig")
        OpenKlant2Config = app.get_model("openklant", "OpenKlant2Config")

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
