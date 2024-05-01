from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template import loader

from open_inwoner.configurations.bootstrap.registry import (
    ConfigSetting,
    ConfigurationRegistry,
)

SUPPORTED_OPTIONS = ConfigurationRegistry.get_field_names()
TEMPLATE_PATH = Path("configurations/config_doc.rst")
TARGET_DIR = Path(settings.BASE_DIR) / "docs" / "configuration"


class ConfigDocBaseCommand(BaseCommand):
    def get_config(self, config_option: str, class_name_only=False) -> ConfigSetting:
        config_model = getattr(ConfigurationRegistry, config_option, None)
        if class_name_only:
            return config_model.__name__

        config_instance = config_model()
        return config_instance

    def get_detailed_info(self, config: ConfigSetting) -> list[list[str]]:
        ret = []
        for field in config.config_fields.all:
            part = []
            part.append(f"{'Variable':<20}{config.get_setting_name(field)}")
            part.append(f"{'Setting':<20}{field.verbose_name}")
            part.append(f"{'Description':<20}{field.description or 'No description'}")
            part.append(f"{'Possible values':<20}{field.values}")
            part.append(f"{'Default value':<20}{field.default_value}")
            ret.append(part)
        return ret

    def format_display_name(self, display_name):
        """Surround title with '=' to display as heading in rst file"""

        heading_bar = "=" * len(display_name)
        display_name_formatted = f"{heading_bar}\n{display_name}\n{heading_bar}"
        return display_name_formatted

    def render_doc(self, config_option: str) -> None:
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
        detailed_info.sort()

        template_variables = {
            "enable_settings": f"{config.namespace}_CONFIG_ENABLE",
            "required_settings": required_settings,
            "all_settings": all_settings,
            "detailed_info": detailed_info,
            "link": f".. _{config_option}:",
            "title": self.format_display_name(config.display_name),
        }

        template = loader.get_template(TEMPLATE_PATH)
        rendered = template.render(template_variables)

        return rendered


class Command(ConfigDocBaseCommand):
    help = "Create docs for configuration setup steps"

    def add_arguments(self, parser):
        parser.add_argument("config_option", nargs="?")

    def write_doc(self, config_option: str) -> None:
        rendered = self.render_doc(config_option)

        output_path = TARGET_DIR / f"{config_option}.rst"

        with open(output_path, "w") as output:
            output.write(rendered)

    def handle(self, *args, **kwargs) -> None:
        config_option = kwargs["config_option"]

        if config_option and config_option not in SUPPORTED_OPTIONS:
            self.stdout.write(f"Unsupported config option ({config_option})\n")
            self.stdout.write(f"Supported: {', '.join(SUPPORTED_OPTIONS)}")
            return
        elif config_option:
            self.write_doc(config_option)
        else:
            for option in SUPPORTED_OPTIONS:
                self.write_doc(option)
