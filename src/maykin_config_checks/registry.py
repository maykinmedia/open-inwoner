class ConfigCheckRegistry:
    def __init__(self):
        self._checks = {}
        self._model_checks = {}

    def register(self, check, model=None):
        self._checks[check.identifier] = check

        if model is not None:
            self._model_checks.setdefault(model, set())
            self._model_checks[model].add(check.identifier)

    def get_checks(self, model=None):
        if model is None:
            return list(self._checks.values())

        identifiers = self._model_checks.get(model, set())

        return [
            self._checks[identifier]
            for identifier in identifiers
        ]

    def get_check(self, identifier):
        return self._checks.get(identifier)


registry = ConfigCheckRegistry()
