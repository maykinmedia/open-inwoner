from django.test import TestCase

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.models import User

from .factories import UserFactory, eHerkenningUserFactory


class UserManagerTests(TestCase):
    def test_create_superuser(self):
        user = User.objects.create_superuser("god@heaven.com", "praisejebus")
        self.assertIsNotNone(user.pk)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertEqual(user.email, "god@heaven.com")
        self.assertTrue(user.check_password("praisejebus"))
        self.assertNotEqual(user.password, "praisejebus")

    def test_create_user(self):
        user = User.objects.create_user("infidel")
        self.assertIsNotNone(user.pk)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.has_usable_password())


class UserQueryTests(TestCase):
    def test_having_usable_email(self):
        expected = [
            UserFactory(first_name="usable_1", email="usable@example.com"),
            UserFactory(first_name="usable_2", email="org-domain@prefix-example.org"),
        ]

        # bad
        UserFactory(first_name="placeholder", email="placeholder@example.org")
        UserFactory(first_name="empty", email="")

        actual = User.objects.having_usable_email()
        self.assertEqual(set(list(actual)), set(expected))


class TestEHerkenningManager(TestCase):
    def setUp(self):
        self.user_kvk_without_vestiging = eHerkenningUserFactory(
            kvk="12345678",
            vestiging="",
        )
        self.user_kvk_with_vestiging = eHerkenningUserFactory(
            kvk="12345678",
            vestiging="00123456789",
        )
        self.another_user_without_kvk_vestiging = eHerkenningUserFactory(
            kvk="87654321",
            vestiging="",
        )

        # Create a regular user (not eHerkenning)
        self.regular_user = UserFactory(
            kvk="12345678", vestiging="", login_type=LoginTypeChoices.default
        )

        self.manager = User.eherkenning_objects

    def test_get_queryset(self):
        """Test that get_queryset only returns eherkenning users"""
        queryset = self.manager.get_queryset()

        # Should return 3 users (all eherkenning users)
        self.assertEqual(
            list(queryset),
            [
                self.user_kvk_without_vestiging,
                self.user_kvk_with_vestiging,
                self.another_user_without_kvk_vestiging,
            ],
        )

        # The regular user should not be in the queryset
        self.assertNotIn(self.regular_user, queryset)

    def test_get_by_kvk(self):
        user = self.manager.get_by_kvk(kvk="12345678")
        self.assertEqual(user, self.user_kvk_without_vestiging)

        user = self.manager.get_by_kvk(kvk="87654321")
        self.assertEqual(user, self.another_user_without_kvk_vestiging)

        # Should raise for non-existent KVK
        with self.assertRaises(User.DoesNotExist):
            self.manager.get_by_kvk(kvk="99999999")

    def test_get_by_kvk_and_vestiging(self):
        """Test retrieving a user by both KVK and vestiging"""
        user = self.manager.get_by_kvk_and_vestiging(kvk="12345678", vestiging="")
        self.assertEqual(user, self.user_kvk_without_vestiging)

        # Test with None vestiging (should default to empty string)
        user = self.manager.get_by_kvk_and_vestiging(kvk="12345678", vestiging=None)
        self.assertEqual(user, self.user_kvk_without_vestiging)

        # Test with specific vestiging
        user = self.manager.get_by_kvk_and_vestiging(
            kvk="12345678", vestiging="00123456789"
        )
        self.assertEqual(user, self.user_kvk_with_vestiging)

        # Should raise for non-existent combination
        with self.assertRaises(User.DoesNotExist):
            self.manager.get_by_kvk_and_vestiging(
                kvk="12345678", vestiging="98765432100"
            )

    def test_filter_by_kvk_and_vestiging(self):
        """Test filtering users by KVK and vestiging"""
        # Test with KVK only, empty vestiging
        queryset = self.manager.filter_by_kvk_and_vestiging(
            kvk="12345678", vestiging=""
        )
        self.assertEqual(list(queryset), [self.user_kvk_without_vestiging])

        # Test with KVK and None vestiging (should default to empty string)
        queryset = self.manager.filter_by_kvk_and_vestiging(
            kvk="12345678", vestiging=None
        )
        self.assertEqual(list(queryset), [self.user_kvk_without_vestiging])

        # Test with KVK and specific vestiging
        queryset = self.manager.filter_by_kvk_and_vestiging(
            kvk="12345678", vestiging="00123456789"
        )
        self.assertEqual(list(queryset), [self.user_kvk_with_vestiging])

        # Test with non-existent combination (should return empty queryset)
        queryset = self.manager.filter_by_kvk_and_vestiging(
            kvk="12345678", vestiging="98765432100"
        )
        self.assertEqual(queryset.count(), 0)

    def test_create(self):
        """Test creating a new eHerkenning user"""
        # Create with KVK only (vestiging defaulting to empty string)
        new_user1 = self.manager.create(kvk="11111111")

        self.assertEqual(new_user1.login_type, LoginTypeChoices.eherkenning)
        self.assertEqual(new_user1.kvk, "11111111")
        self.assertEqual(new_user1.vestiging, "")
        self.assertEqual(new_user1.email, "user-11111111@localhost")

        # Create with both KVK and vestiging
        new_user2 = self.manager.create(kvk="22222222", vestiging="12345678901")

        self.assertEqual(new_user2.login_type, LoginTypeChoices.eherkenning)
        self.assertEqual(new_user2.kvk, "22222222")
        self.assertEqual(new_user2.vestiging, "12345678901")
        self.assertEqual(new_user2.email, "user-22222222@localhost")

        # Create with explicit None vestiging (should convert to empty string)
        new_user3 = self.manager.create(kvk="33333333", vestiging=None)

        self.assertEqual(new_user3.login_type, LoginTypeChoices.eherkenning)
        self.assertEqual(new_user3.kvk, "33333333")
        self.assertEqual(new_user3.vestiging, "")
        self.assertEqual(new_user3.email, "user-33333333@localhost")
