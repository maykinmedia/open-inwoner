import factory
import factory.faker


class ForeignKeyRef(factory.Factory):
    class Meta:
        model = dict

    uuid = factory.Faker("uuid4")
