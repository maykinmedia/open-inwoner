import factory
import factory.faker
from factory import fuzzy

from openklant2.factories.common import ForeignKeyRef
from openklant2.factories.helpers import validator
from openklant2.types.iso_639_2 import LanguageCode
from openklant2.types.resources.partij import (
    CreatePartijContactpersoonDataValidator,
    CreatePartijOrganisatieDataValidator,
    CreatePartijPersoonDataValidator,
)


class ContactnaamFactory(factory.Factory):
    class Meta:
        model = dict

    voorletters = factory.Faker("prefix")
    voornaam = factory.Faker("first_name")
    voorvoegselAchternaam = factory.Faker("prefix")
    achternaam = factory.Faker("last_name")


class PartijIdentificatieOrganisatieFactory(factory.Factory):
    class Meta:
        model = dict

    naam = factory.Faker("company")


class PartijIdentificatiePersoonFactory(factory.Factory):
    class Meta:
        model = dict

    contactnaam = factory.SubFactory(ContactnaamFactory)


class PartijIdentificatieContactpersoonFactory(factory.Factory):
    class Meta:
        model = dict

    class Params:
        werkte_voor_partij = None

    contactnaam = factory.SubFactory(ContactnaamFactory)
    werkteVoorPartij = factory.SubFactory(ForeignKeyRef)


class CreatePartijBaseFactory(factory.Factory):
    class Meta:
        model = dict
        abstract = True

    digitaleAdressen = None
    voorkeursDigitaalAdres = None
    rekeningnummers = None
    voorkeursRekeningnummer = None
    indicatieGeheimhouding = fuzzy.FuzzyChoice([True, False])
    indicatieActief = fuzzy.FuzzyChoice([True, False])
    voorkeurstaal = fuzzy.FuzzyChoice(LanguageCode.__args__)


@validator(CreatePartijPersoonDataValidator)
class CreatePartijPersoonDataFactory(CreatePartijBaseFactory):
    class Meta:
        model = dict

    soortPartij = "persoon"
    partijIdentificatie = factory.SubFactory(PartijIdentificatiePersoonFactory)


@validator(CreatePartijOrganisatieDataValidator)
class CreatePartijOrganisatieDataFactory(CreatePartijBaseFactory):
    class Meta:
        model = dict

    soortPartij = "organisatie"
    partijIdentificatie = factory.SubFactory(PartijIdentificatieOrganisatieFactory)


@validator(CreatePartijContactpersoonDataValidator)
class CreatePartijContactPersoonDataFactory(CreatePartijBaseFactory):
    class Meta:
        model = dict

    soortPartij = "contactpersoon"
    partijIdentificatie = factory.SubFactory(PartijIdentificatieContactpersoonFactory)
