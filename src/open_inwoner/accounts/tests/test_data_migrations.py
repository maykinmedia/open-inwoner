from open_inwoner.utils.tests.test_migrations import TestMigrations


class RemoveContactMigrationTests(TestMigrations):
    app = "accounts"
    migrate_from = "0048_auto_20221205_0921"
    migrate_to = "0049_auto_20221205_0921"

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
        ContactModel.objects.create(
            first_name="Vas",
            last_name="Jodys",
            created_by=self.user,
            contact_user=self.contact_user,
        )

        # Create invite
        InviteModel = apps.get_model("accounts", "Invite")
        self.invite = InviteModel.objects.create(
            inviter=self.user, invitee=self.contact_user
        )

    def test_uuid_is_added(self):
        self.assertIsNone(self.user.uuid)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.uuid)

    def test_user_contacts_is_updated_with_existing_contact(self):
        self.user.refresh_from_db()
        self.assertEqual(list(self.user.user_contacts.all()), [self.contact_user])

    def test_invite_names_are_updated_from_invitee_user_data(self):
        self.invite.refresh_from_db()
        self.assertEqual(self.invite.invitee_first_name, self.contact_user.first_name)
        self.assertEqual(self.invite.invitee_last_name, self.contact_user.last_name)
