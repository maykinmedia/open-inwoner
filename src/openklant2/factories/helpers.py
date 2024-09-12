import factory
from pydantic import TypeAdapter


def validator(validator: TypeAdapter):
    def decorator(cls: type[factory.Factory]):
        @factory.post_generation
        def validate(obj, *args, **kwargs):
            validator.validate_python(obj)

        setattr(cls, "post_generation_validator", validate)

        return cls

    return decorator
