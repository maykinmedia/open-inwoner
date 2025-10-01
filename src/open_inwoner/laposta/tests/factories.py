from polyfactory.factories.pydantic_factory import ModelFactory

from open_inwoner.laposta.api_models import LapostaList, Member


class LapostaListFactory(ModelFactory[LapostaList]):
    __model__ = LapostaList


class MemberFactory(ModelFactory[Member]):
    __model__ = Member
