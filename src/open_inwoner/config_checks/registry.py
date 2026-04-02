from collections import defaultdict


class ConfigCheckRegistry:
    def __init__(self):
        self._registry = defaultdict(dict)

    def register(self, model, check):
        identifier = check.identifier

        if identifier in self._registry[model]:
            if self._registry[model][identifier] == check:
                return

            raise ValueError(
                f"Duplicate identifier {identifier} for model {model.__name__}"
            )

        self._registry[model][identifier] = check

    def get_checks(self, model):
        return list(self._registry.get(model, {}).values())

    def get_check_by_identifier(self, model, identifier):
        return self._registry.get(model, {}).get(identifier)


registry = ConfigCheckRegistry()
