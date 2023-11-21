from digid_eherkenning.managers import BaseeHerkenningManager as _BaseeHerkenningManager


class BaseeHerkenningManager(_BaseeHerkenningManager):
    def get_by_kvk(self, kvk):
        raise NotImplementedError
