from polyfactory.factories.pydantic_factory import ModelFactory

from ..client import Appointment, BranchDetailDict


class BranchDetailFactory(ModelFactory[BranchDetailDict]):
    __model__ = BranchDetailDict


class AppointmentFactory(ModelFactory[Appointment]):
    __model__ = Appointment
