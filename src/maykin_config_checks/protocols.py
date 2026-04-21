from typing import Any, Generic, Optional, Protocol, TypeVar

from django.db.models import Model
from django.forms import Form
from django.http import HttpRequest

from . import GenericConfigCheckResult

TCleanedData = TypeVar(
    "TCleanedData",
    bound=dict[str, Any],
    contravariant=True,
)

TModel = TypeVar(
    "TModel",
    bound=Model,
)


class InteractiveConfigCheck(
    Protocol,
    Generic[TCleanedData, TModel],
):
    identifier: str
    label: str
    form_class: type[Form]

    @classmethod
    def get_form_kwargs(
        cls,
        instance: Optional[TModel] = None,
    ) -> dict[str, Any]:
        ...

    def run(
        self,
        data: TCleanedData,
        instance: Optional[TModel] = None,
        request: Optional[HttpRequest] = None,
    ) -> GenericConfigCheckResult:
        ...
