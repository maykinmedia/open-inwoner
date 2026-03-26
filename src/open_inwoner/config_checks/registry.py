from collections import defaultdict


class ConfigCheckRegistry:
    def __init__(self):
        self._registry = defaultdict(list)

    def register(self, model, check):
        self._registry[model].append(check)

    def get_checks(self, model):
        return self._registry.get(model, [])


registry = ConfigCheckRegistry()
