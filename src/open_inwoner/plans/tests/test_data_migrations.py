from open_inwoner.utils.tests.test_migrations import TestMigrations


class RemoveContactMigrationTests(TestMigrations):
    app = "plans"
    migrate_from = "0009_plan_plan_contacts"
    migrate_to = "0010_auto_20221130_1611"

    def setUpBeforeMigration(self, apps):
        # Create user
        UserModel = apps.get_model("accounts", "User")
        self.user = UserModel.objects.create(
            first_name="Joe",
            last_name="Kirts",
            email="user@example.com",
            password="secret",
        )

        # Create contact
        ContactModel = apps.get_model("accounts", "Contact")
        self.contact_user = UserModel.objects.create(
            first_name="Jim",
            last_name="Aklisert",
            email="user2@example.com",
            password="secret",
        )
        self.contact = ContactModel.objects.create(
            first_name="Vas",
            last_name="Jodys",
            created_by=self.user,
            contact_user=self.contact_user,
        )

        # Create Plan
        PlanModel = apps.get_model("plans", "Plan")
        self.plan = PlanModel.objects.create(
            title="A title",
            goal="some text",
            end_date="2021-01-10",
            created_by=self.user,
        )
        self.plan.contacts.add(self.contact)

    def test_plan_contacts_is_updated_with_existing_contact(self):
        self.plan.refresh_from_db()
        self.assertEqual(list(self.plan.plan_contacts.all()), [self.contact_user])
