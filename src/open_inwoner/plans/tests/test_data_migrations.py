from open_inwoner.utils.tests.test_migrations import TestMigrations


class RemoveContactMigrationTests(TestMigrations):
    app = "plans"
    migrate_from = "0009_plan_plan_contacts"
    migrate_to = "0010_auto_20221205_0921"

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


class PlanContactThroughModelMigrationTests(TestMigrations):
    app = "plans"
    migrate_from = "0013_auto_20230223_1115"
    migrate_to = "0015_plancontact_notify_new"

    extra_migrate_from = [("accounts", "0055_user_image")]

    def setUpBeforeMigration(self, apps):
        UserModel = apps.get_model("accounts", "User")
        self.user = UserModel.objects.create(
            email="user@example.com",
        )
        self.other_user = UserModel.objects.create(
            email="other_user@example.com",
        )

        PlanModel = apps.get_model("plans", "Plan")
        self.plan = PlanModel.objects.create(
            title="A title",
            end_date="2021-01-10",
            created_by=self.user,
        )
        self.plan.plan_contacts.add(self.other_user)

    def test_plan_contacts_still_exist(self):
        UserModel = self.apps.get_model("accounts", "User")
        PlanModel = self.apps.get_model("plans", "Plan")
        PlanContact = self.apps.get_model("plans", "PlanContact")

        other_user = UserModel.objects.get(id=self.other_user.id)
        plan = PlanModel.objects.get(id=self.plan.id)
        self.assertEqual(list(plan.plan_contacts.all()), [other_user])

        # check we don't notify existing contacts
        contact = PlanContact.objects.get()
        self.assertEqual(contact.notify_new, False)
