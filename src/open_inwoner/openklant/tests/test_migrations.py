from django.db import connection
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
class ContactFormConfigMigrationTest(TestSuccessfulMigrations):
    migrate_from = "0027_alter_klantensysteemconfig_primary_backend"
    migrate_to = "0028_change_contactformconfig_descriptions"
    app = "openklant"

    def setUpBeforeMigration(self, apps):
        Placeholder = apps.get_model("cms", "Placeholder")

        # Create a placeholder for the CMS plugin
        placeholder = Placeholder.objects.create(slot="test")

        # Use raw SQL to insert plugin records, bypassing the historical model
        # that expects treebeard fields (depth, path, numchild) which don't exist in CMS 4.x
        with connection.cursor() as cursor:
            # Insert base CMSPlugin record
            cursor.execute(
                """
                INSERT INTO cms_cmsplugin
                (id, placeholder_id, language, plugin_type, position, creation_date, changed_date, parent_id)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW(), NULL)
                """,
                (1, placeholder.id, "nl", "ContactFormPlugin", 0),
            )

            # Insert ContactFormConfig data
            cursor.execute(
                """
                INSERT INTO openklant_contactformconfig
                (cmsplugin_ptr_id, description)
                VALUES (%s, %s)
                """,
                (1, "Old contactform description"),
            )

            self.config_id = 1

    def test_migrate_contactform_description(self):
        # Use raw SQL to query the migrated data, bypassing the ORM which
        # uses the historical model with treebeard fields that don't exist in CMS 4.x
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT description_authenticated_user, description_anonymous_user
                FROM openklant_contactformconfig
                WHERE cmsplugin_ptr_id = %s
                """,
                (self.config_id,),
            )
            row = cursor.fetchone()
            self.assertIsNotNone(row, "ContactFormConfig should exist after migration")

            description_authenticated, description_anonymous = row
            self.assertEqual(description_authenticated, "Old contactform description")
            self.assertEqual(description_anonymous, "Old contactform description")
