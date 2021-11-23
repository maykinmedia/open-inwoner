from typing import List, Type

from drf_spectacular.plumbing import force_instance
from drf_spectacular.utils import OpenApiParameter
from rest_framework import serializers


def input_serializer_to_parameters(
    serializer_class: Type[serializers.Serializer],
) -> List[OpenApiParameter]:
    serializer = force_instance(serializer_class)
    parameters = []

    for field in serializer.fields.values():
        if isinstance(field, serializers.HiddenField):
            continue

        if isinstance(field, serializers.Serializer):
            # querystring parameters only accept flat structures
            continue

        parameter = OpenApiParameter(
            name=field.field_name,
            type=str,
            location=OpenApiParameter.QUERY,
            required=field.required,
            description=field.help_text,
            enum=getattr(field, "choices", None),
        )
        parameters.append(parameter)

    return parameters
