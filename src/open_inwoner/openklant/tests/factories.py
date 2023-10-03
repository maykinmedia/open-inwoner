import factory


class ContactFormSubjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "openklant.ContactFormSubject"

    subject = factory.Faker("sentence")
    subject_code = factory.Faker("word")
