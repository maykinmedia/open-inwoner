import factory
import factory.fuzzy

from openklant2.factories.common import IdentificationNumber
from openklant2.factories.helpers import validator
from openklant2.types.resources.actor import CreateActorDataValidator


class ActorIdentificatorFactory(factory.Factory):
    class Meta:
        model = dict

    objectId = IdentificationNumber()
    codeObjecttype = factory.Faker("word")
    codeRegister = factory.Faker("word")
    codeSoortObjectId = factory.Faker("word")


@validator(CreateActorDataValidator)
class CreateActorDataFactory(factory.Factory):
    class Meta:
        model = dict

    naam = factory.Faker("name")
    soortActor = factory.fuzzy.FuzzyChoice(
        ["medewerker", "geautomatiseerde_actor", "organisatorische_eenheid"]
    )
    indicatieActief = True
    actoridentificator = factory.SubFactory(ActorIdentificatorFactory)
