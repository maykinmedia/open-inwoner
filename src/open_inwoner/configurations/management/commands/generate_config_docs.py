import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template import loader

from open_inwoner.configurations.bootstrap.models import ConfigurationSettingsMap
from open_inwoner.configurations.bootstrap.typing import ConfigSetting

SUPPORTED_OPTIONS = ConfigurationSettingsMap.get_field_names()
TEMPLATE_PATH = Path("configurations/config_doc.rst")
TARGET_DIR = Path(settings.BASE_DIR) / "docs" / "configuration"


class Command(BaseCommand):
    help = "Create docs for configuration setup steps"

    def add_arguments(self, parser):
        parser.add_argument("config_option", nargs="?")

    def get_config(self, config_option: str) -> ConfigSetting:
        config_model = getattr(ConfigurationSettingsMap, config_option, None)
        config_instance = config_model()
        return config_instance

    def get_detailed_info(self, config: ConfigSetting) -> list[list[str]]:
        ret = []
        for field in config.config_fields.all:
            part = []
            part.append(f"{'Variable':<20}{config.get_setting_name(field)}")
            part.append(f"{'Setting':<20}{field.verbose_name}")
            part.append(f"{'Description':<20}{field.description or 'No description'}")
            part.append(f"{'Possible values':<20}{field.values or 'No information'}")
            part.append(f"{'Default value':<20}{field.default_value or 'No default'}")
            ret.append(part)
        return ret

    def format_display_name(self, display_name):
        """Surround title with '=' to display as heading in rst file"""

        heading_bar = f"{'=' * len(display_name)}"
        display_name_formatted = (
            heading_bar + "\n" + f"{display_name}" + "\n" + heading_bar
        )
        return display_name_formatted

    def write_file_from_template(
        self,
        template_path: os.PathLike,
        template_variables: dict[str, list],
        output_path: os.PathLike,
    ):
        template = loader.get_template(template_path)
        rendered = template.render(template_variables)

        with open(output_path, "w") as output:
            output.write(rendered)

    def generate_single_doc(self, config_option: str) -> None:
        config = self.get_config(config_option)

        required_settings = [
            config.get_setting_name(field) for field in config.config_fields.required
        ]
        required_settings.sort()
        all_settings = [
            config.get_setting_name(field) for field in config.config_fields.all
        ]
        all_settings.sort()
        detailed_info = self.get_detailed_info(config)

        template_variables = {
            "required_settings": required_settings,
            "all_settings": all_settings,
            "detailed_info": detailed_info,
            "link": f".. _{config_option}:",
            "title": self.format_display_name(config.display_name),
        }
        template_path = TEMPLATE_PATH
        output_path = TARGET_DIR / f"{config_option}.rst"

        self.write_file_from_template(template_path, template_variables, output_path)

    def handle(self, *args, **kwargs) -> None:
        config_option = kwargs["config_option"]

        if config_option and config_option not in SUPPORTED_OPTIONS:
            self.stdout.write(f"Unsupported config option ({config_option})\n")
            self.stdout.write(f"Supported: {', '.join(SUPPORTED_OPTIONS)}")
            return
        elif config_option:
            self.generate_single_doc(config_option)
        else:
            for option in SUPPORTED_OPTIONS:
                self.generate_single_doc(option)
