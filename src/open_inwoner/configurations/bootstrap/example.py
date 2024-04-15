from abc import ABC
from typing import Any


class Value:
    """
    untyped descriptor

    https://docs.python.org/3/howto/descriptor.html

    typed version for later
    """

    type: type

    # some attribute suggestions
    verbose_name: str = ""
    help_text: str = ""
    example: str = ""  # could be a list?
    model_field: str = ""
    default: Any = None

    # needed
    public_name: str

    def __init__(self, type, verbose_name=""):
        self.type = type
        self.verbose_name = verbose_name
        # add other attributes here

    def __set_name__(self, owner, name):
        # public name is the name of the attribute
        # private_name is prefixed name where we can store data on the instance
        self.public_name = name
        self.private_name = "_" + name

    def __get__(self, obj, objtype=None):
        # allow override per instance (for tests etc)
        if hasattr(obj, self.private_name):
            return getattr(obj, self.private_name)

        # tmp
        value = 123
        # read the actual value using config util (add more arguments like default etc)
        # value = utils.config(self.get_env_name())
        return value

    def __set__(self, obj, value):
        assert isinstance(obj, self.type)
        setattr(obj, self.private_name, value)

    # useful methods example
    def get_env_name(self):
        # convert to env-var name
        return self.public_name.upper()


class ConfSettingsBase(ABC):
    """
    base class
    """

    @classmethod
    def dump_help(cls):
        ret = []
        for name, descriptor in cls.iter_descriptors():
            # output documentation, more here
            ret.append(f"{name}: {descriptor.verbose_name}")
        return "\n".join(ret)

    @classmethod
    def iter_descriptors(cls):
        for name, member in dict(cls.__dict__).items():
            if name.startswith("_"):
                continue
            if not isinstance(member, Value):
                continue
            # yield something useful, like the name and descriptor instance
            yield name, member


class SiteConfigurationSettings(ConfSettingsBase):
    api_root = Value(
        str,
        verbose_name="API Root",
        # help_text="Sets the api root",
        # example="http://xyz",
        # etc etc
    )
    some_boolean_option = Value(
        bool,
        verbose_name="My Bool",
        # help_text="Foo bar",
        # example="True",
        # default=False,
        # etc etc
    )


# site = SiteConfigurationSettings()
# print(site.api_root)
# print(site.some_boolean_option)
#
# print(SiteConfigurationSettings.dump_help())
