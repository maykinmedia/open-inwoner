from django.test import TestCase

from ..models import User
from .factories import UserFactory


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
        UserFactory(first_name="placeholder", email="placeholder@example.org"),
        UserFactory(first_name="empty", email="")

        actual = User.objects.having_usable_email()
        self.assertEqual(list(actual), expected)
