from polyfactory.factories.pydantic_factory import ModelFactory

from open_inwoner.qmatic.client import Appointment, BranchDetail, QmaticService


class BranchDetailFactory(ModelFactory[BranchDetail]):
    __model__ = BranchDetail


class AppointmentFactory(ModelFactory[Appointment]):
    __model__ = Appointment


class QmaticServiceFactory(ModelFactory[QmaticService]):
    __model__ = QmaticService
