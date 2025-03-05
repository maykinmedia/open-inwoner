from digid_eherkenning.managers import BaseeHerkenningManager as _BaseeHerkenningManager


class BaseeHerkenningManager(_BaseeHerkenningManager):
    def get_by_kvk(self, kvk: str):
        raise NotImplementedError

    def get_by_kvk_and_vestiging(self, *, kvk: str, vestiging: str | None):
        raise NotImplementedError

    def filter_by_kvk_and_vestiging(self, *, kvk: str, vestiging: str | None):
        raise NotImplementedError
