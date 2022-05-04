from datetime import datetime, timezone
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile

import factory
import factory.fuzzy


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "accounts.User"

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.LazyAttributeSequence(
        lambda a, n: "{0}.{1}-{2}@example.com".format(
            a.first_name.lower(), a.last_name.lower(), n
        )
    )
    password = factory.PostGenerationMethodCall("set_password", "secret")


class TokenFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "authtoken.Token"
        exclude = ("created_for",)

    created_for = factory.SubFactory(UserFactory)
    key = factory.LazyAttribute(lambda o: uuid4())
    user_id = factory.LazyAttribute(lambda o: o.created_for.id)


class ContactFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "accounts.Contact"

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
    phonenumber = "0612345678"
    created_by = factory.SubFactory(UserFactory)
    contact_user = factory.SubFactory(UserFactory)


class AppointmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "accounts.Appointment"

    name = factory.Faker("first_name")
    datetime = factory.fuzzy.FuzzyDateTime(datetime.now(timezone.utc))
    created_by = factory.SubFactory(UserFactory)


class ActionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "accounts.Action"

    name = factory.Faker("first_name")
    created_by = factory.SubFactory(UserFactory)


class DocumentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "accounts.Document"

    name = factory.Faker("first_name")
    file = SimpleUploadedFile("file.jpg", b"file_content", content_type="image/jpeg")
    owner = factory.SubFactory(UserFactory)


class MessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "accounts.Message"

    sender = factory.SubFactory(UserFactory)
    receiver = factory.SubFactory(UserFactory)
    content = factory.Faker("text")
    seen = False

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        created_on = kwargs.pop("created_on", None)
        obj = super()._create(target_class, *args, **kwargs)
        if created_on is not None:
            obj.created_on = created_on
            obj.save()
        return obj


class InviteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "accounts.Invite"

    contact = factory.SubFactory(ContactFactory)
    inviter = factory.LazyAttribute(lambda o: o.contact.created_by)
    invitee = factory.LazyAttribute(lambda o: o.contact.contact_user)
