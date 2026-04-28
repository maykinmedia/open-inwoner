from collections import defaultdict
from typing import Any, Dict, List, Optional, Protocol, Type, runtime_checkable

from django.db.models import Model
from django.forms import Form

from open_inwoner.config_checks.permissions import BasePermission


@runtime_checkable
class ConfigCheck(Protocol):
    identifier: str
    label: str
    form_class: Type[Form]
    required_permissions: tuple[BasePermission, ...]

    @classmethod
    def get_form_kwargs(cls, obj: Model | None) -> dict[str, Any]: ...

    def run(self, form: Form, obj: Model | None = None) -> Any: ...


class ConfigCheckRegistry:
    def __init__(self) -> None:
        self._registry: Dict[Type[Model], Dict[str, Type[ConfigCheck]]] = defaultdict(
            dict
        )

    def register(self, model: Type[Model], check: Type[ConfigCheck]) -> None:
        identifier: str = check.identifier

        if identifier in self._registry[model]:
            if self._registry[model][identifier] == check:
                return

            raise ValueError(
                f"Duplicate identifier {identifier} for model {model.__name__}"
            )

        self._registry[model][identifier] = check

    def get_checks(self, model: Type[Model]) -> List[Type[ConfigCheck]]:
        return list(self._registry.get(model, {}).values())

    def get_check_by_identifier(
        self, model: Type[Model], identifier: str
    ) -> Optional[Type[ConfigCheck]]:
        return self._registry.get(model, {}).get(identifier)


registry: ConfigCheckRegistry = ConfigCheckRegistry()
