import random

import factory
import factory.faker
from faker import Faker

from openklant2.factories.common import ForeignKeyRef
from openklant2.factories.helpers import validator
from openklant2.types.resources.digitaal_adres import CreateDigitaalAdresDataValidator

fake = Faker("nl_NL")


@validator(CreateDigitaalAdresDataValidator)
class CreateDigitaalAdresDataFactory(factory.Factory):
    class Meta:
        model = dict

    adres = factory.LazyAttribute(
        lambda obj: (
            fake.email()
            if obj.soortDigitaalAdres == "email"
            else (
                "0912345678"
                if obj.soortDigitaalAdres == "telefoonnummer"
                else fake.address()
            )
        )
    )
    omschrijving = factory.Faker("word")
    soortDigitaalAdres = random.choice(  # noqa: S311
        ["email", "telefoonnummer", "overig"],
    )
    verstrektDoorBetrokkene = factory.SubFactory(ForeignKeyRef)
    verstrektDoorPartij = factory.SubFactory(ForeignKeyRef)
