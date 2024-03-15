import factory
from polyfactory.factories.pydantic_factory import ModelFactory

from open_inwoner.accounts.tests.factories import UserFactory

from ..api_models import LapostaList, Member
from ..models import Subscription


class LapostaListFactory(ModelFactory[LapostaList]):
    __model__ = LapostaList


class MemberFactory(ModelFactory[Member]):
    __model__ = Member


class SubscriptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Subscription

    user = factory.SubFactory(UserFactory)
