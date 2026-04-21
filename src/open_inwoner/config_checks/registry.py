class ConfigCheckRegistry:
    def __init__(self):
        self._registry = {}

    def register(self, model, check):
        self._registry.setdefault(model, {})
        self._registry[model][check.identifier] = check

    def get_checks(self, model):
        return list(self._registry.get(model, {}).values())

    def get_check(self, model, identifier):
        return self._registry.get(model, {}).get(identifier)


registry = ConfigCheckRegistry()
