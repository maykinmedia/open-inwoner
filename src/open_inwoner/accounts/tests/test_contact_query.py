from django.test import TestCase

from ..models import Contact
from .factories import ContactFactory, UserFactory


class ContactExtendedTests(TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.me = UserFactory.create()

    def test_no_contact(self):
        contacts = Contact.objects.get_extended_contacts_for_user(self.me)

        self.assertEqual(contacts.count(), 0)

    def test_mine_contact(self):
        other_user = UserFactory.create()
        contact = ContactFactory.create(
            created_by=self.me, contact_user=other_user, email=other_user.email
        )

        contacts = Contact.objects.get_extended_contacts_for_user(self.me)

        self.assertEqual(contacts.count(), 1)

        extended_contact = contacts.get()
        self.assertEqual(extended_contact.id, contact.id)
        self.assertEqual(extended_contact.other_user_id, other_user.id)
        self.assertFalse(extended_contact.reverse)
        self.assertEqual(extended_contact.other_user_email, contact.email)
        self.assertEqual(extended_contact.other_user_first_name, contact.first_name)
        self.assertEqual(extended_contact.other_user_last_name, contact.last_name)

    def test_reverse_contact(self):
        other_user = UserFactory.create()
        contact = ContactFactory.create(
            created_by=other_user, contact_user=self.me, email=self.me.emaill
        )

        contacts = Contact.objects.get_extended_contacts_for_user(self.me)

        self.assertEqual(contacts.count(), 1)

        extended_contact = contacts.get()
        self.assertEqual(extended_contact.id, contact.id)
        self.assertEqual(extended_contact.other_user_id, self.me.id)
        self.assertTrue(extended_contact.reverse)
        self.assertEqual(extended_contact.other_user_email, self.me.email)
        self.assertEqual(extended_contact.other_user_first_name, self.me.first_name)
        self.assertEqual(extended_contact.other_user_last_name, self.me.last_name)

    def test_mine_and_reverse_contact(self):
        other_user = UserFactory.create()
        direct_contact = ContactFactory.create(
            created_by=self.me, contact_user=other_user, email=other_user.email
        )
        reverse_contact = ContactFactory.create(
            created_by=other_user, contact_user=self.me, email=self.me.email
        )

        contacts = Contact.objects.get_extended_contacts_for_user(self.me)

        self.assertEqual(contacts.count(), 1)

        extended_contact = contacts.get()
        self.assertEqual(extended_contact.id, direct_contact.id)
        self.assertEqual(extended_contact.other_user_id, other_user.id)
        self.assertFalse(extended_contact.reverse)
        self.assertEqual(extended_contact.other_user_email, direct_contact.email)
        self.assertEqual(
            extended_contact.other_user_first_name, direct_contact.first_name
        )
        self.assertEqual(
            extended_contact.other_user_last_name, direct_contact.last_name
        )
