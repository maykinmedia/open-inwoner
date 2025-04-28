import factory
import factory.fuzzy

from openklant2.factories.helpers import validator
from openklant2.types.resources.interne_taak import CreateInterneTaakDataValidator


@validator(CreateInterneTaakDataValidator)
class CreateInterneTaakFactory(factory.Factory):
    class Meta:
        model = dict

    nummer = factory.LazyAttributeSequence(lambda o, n: f"{n + 1:010d}")
    gevraagdeHandeling = factory.Faker("word")
    aanleidinggevendKlantcontact = None
    toegewezenAanActor = None
    status = factory.fuzzy.FuzzyChoice(["te_verwerken", "verwerkt"])
