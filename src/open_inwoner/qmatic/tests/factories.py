from polyfactory.factories.pydantic_factory import ModelFactory

from ..client import Appointment, BranchDetail


class BranchDetailFactory(ModelFactory[BranchDetail]):
    __model__ = BranchDetail


class AppointmentFactory(ModelFactory[Appointment]):
    __model__ = Appointment
