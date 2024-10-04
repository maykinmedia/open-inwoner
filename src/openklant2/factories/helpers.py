from typing import get_args

import factory
import factory.fuzzy
from pydantic import TypeAdapter


def validator(validator: TypeAdapter):
    def decorator(cls: type[factory.Factory]):
        @factory.post_generation
        def validate(obj, *args, **kwargs):
            validator.validate_python(obj)

        setattr(cls, "post_generation_validator", validate)

        return cls

    return decorator


def _get_literal_options(literal_type):
    return [str(option) for option in get_args(literal_type)]


FuzzyLiteral = lambda literal: factory.fuzzy.FuzzyChoice(_get_literal_options(literal))
