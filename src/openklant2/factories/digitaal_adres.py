import factory
import factory.faker

from openklant2.factories.common import ForeignKeyRef
from openklant2.factories.helpers import validator
from openklant2.types.resources.digitaal_adres import CreateDigitaalAdresDataValidator


@validator(CreateDigitaalAdresDataValidator)
class CreateDigitaalAdresDataFactory(factory.Factory):
    class Meta:
        model = dict

    adres = factory.Faker("address")
    omschrijving = factory.Faker("word")
    soortDigitaalAdres = factory.Faker("word")
    verstrektDoorBetrokkene = factory.SubFactory(ForeignKeyRef)
    verstrektDoorPartij = factory.SubFactory(ForeignKeyRef)
