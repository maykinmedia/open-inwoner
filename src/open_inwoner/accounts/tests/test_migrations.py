from django.db.models import F
from django.db.utils import IntegrityError
from django.test import tag

from open_inwoner.utils.tests.test_migrations import TestSuccessfulMigrations


@tag("migrations")
class UserMigrationTest(TestSuccessfulMigrations):
    migrate_from = "0080_user_phonenumber_alternative"
    migrate_to = (
        "0081_user_check_alternative_phonenumber_differs_from_primary_phonenumber"
    )
    app = "accounts"

    def setUpBeforeMigration(self, apps):
        User = apps.get_model("accounts", "User")

        user = User.objects.create(phonenumber="0612345678")

        # no IntegrityError before migration
        user.phonenumber_alternative = user.phonenumber
        user.save()

    def test_migrate_phonenumber_constraint(self):
        User = self.apps.get_model("accounts", "User")

        self.assertFalse(User.objects.filter(phonenumber=F("phonenumber_alternative")))

        user = User.objects.first()

        with self.assertRaises(IntegrityError):
            user.phonenumber_alternative = user.phonenumber
            user.save()
