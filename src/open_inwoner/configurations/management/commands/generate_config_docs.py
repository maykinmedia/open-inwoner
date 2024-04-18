import os
from pathlib import Path
from typing import TypeAlias

from django.conf import settings
from django.core.management.base import BaseCommand

from jinja2 import Environment, FileSystemLoader, select_autoescape

from open_inwoner.configurations.bootstrap.models import (
    DigiDOIDCConfigurationSettings,
    KICConfigurationSettings,
    SiteConfigurationSettings,
    ZGWConfigurationSettings,
    eHerkenningDOIDCConfigurationSettings,
)

ConfigSetting: TypeAlias = (
    DigiDOIDCConfigurationSettings
    | KICConfigurationSettings
    | SiteConfigurationSettings
    | ZGWConfigurationSettings
    | eHerkenningDOIDCConfigurationSettings
)


SUPPORTED_OPTIONS = ["siteconfig", "kic", "zgw", "digid_oidc", "eherkenning_oidc"]

TEMPLATE_DIR = (
    Path(os.path.abspath(os.path.dirname(__file__))).parent.parent
    / "bootstrap"
    / "templates"
)
TARGET_DIR = Path(settings.BASE_DIR) / "docs" / "configuration"


class Command(BaseCommand):
    help = "Create docs for configuration setup steps"

    def add_arguments(self, parser):
        parser.add_argument("config_option", nargs="?")

    def get_config(self, config_option: str) -> dict[str, ConfigSetting]:
        mapping = {
            "siteconfig": SiteConfigurationSettings,
            "kic": KICConfigurationSettings,
            "zgw": ZGWConfigurationSettings,
            "digid_oidc": DigiDOIDCConfigurationSettings,
            "eherkenning_oidc": eHerkenningDOIDCConfigurationSettings,
        }
        return mapping[config_option]

    def get_detailed_info(self, config: ConfigSetting) -> list[str]:
        ret = []
        for field in config.fields["all"]:
            model_field = config.model._meta.get_field(field.name)
            part = []
            part.append(f"{'Variable':<20}{config.get_setting_name(field)}")
            part.append(f"{'Setting':<20}{str(model_field.verbose_name)}")
            part.append(f"{'Description':<20}{str(model_field.help_text)}")
            part.append(f"{'Model field type':<20}{field.field_type}")
            part.append(f"{'Possible values':<20}{field.values}")
            part.append(f"{'Default value':<20}{field.default_value}")
            ret.append(part)
        return ret

    def write_file_from_template(
        self,
        template_path: os.PathLike,
        template_variables: dict[str, list],
        output_path: os.PathLike,
    ):
        with open(template_path, "r") as template:
            template_str = template.read()
            template = Environment(
                loader=FileSystemLoader(TEMPLATE_DIR), autoescape=select_autoescape()
            ).from_string(template_str)
            rendered = template.render(template_variables)

            with open(output_path, "w") as output:
                output.write(rendered)

    def generate_single_doc(self, config_option: str) -> None:
        config = self.get_config(config_option)

        required_settings = [
            config.get_setting_name(field) for field in config.fields["required"]
        ]
        required_settings.sort()
        all_settings = [
            config.get_setting_name(field) for field in config.fields["all"]
        ]
        all_settings.sort()
        detailed_info = self.get_detailed_info(config)
        template_variables = {
            "required_settings": required_settings,
            "all_settings": all_settings,
            "detailed_info": detailed_info,
        }

        template_path = TEMPLATE_DIR / f"{config_option}.rst.template"
        output_path = TARGET_DIR / f"{config_option}.rst"

        self.write_file_from_template(template_path, template_variables, output_path)

    def handle(self, *args, **kwargs) -> None:
        config_option = kwargs["config_option"]

        if config_option and config_option not in SUPPORTED_OPTIONS:
            return
        elif config_option:
            self.generate_single_doc(config_option)
        else:
            for option in SUPPORTED_OPTIONS:
                self.generate_single_doc(option)
