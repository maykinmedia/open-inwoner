import os
from pathlib import Path

from django.core.management.base import BaseCommand

from jinja2 import Environment, FileSystemLoader

from open_inwoner.configurations.bootstrap.models import (
    DigiDOIDCConfigurationSettings,
    KICConfigurationSettings,
    SiteConfigurationSettings,
    ZGWConfigurationSettings,
    eHerkenningDOIDCConfigurationSettings,
)

SUPPORTED_OPTIONS = ["siteconfig", "kic", "zgw", "digid_oidc", "eherkenning_oidc"]

TEMPLATE_DIR = (
    Path(os.path.abspath(os.path.dirname(__file__))).parent.parent
    / "bootstrap"
    / "templates"
)
TARGET_DIR = (
    Path(os.path.abspath(os.path.dirname(__file__))).parent.parent.parent.parent.parent
    / "docs"
    / "configuration"
)


class Command(BaseCommand):
    help = "Create docs for configuration setup steps"

    def add_arguments(self, parser):
        parser.add_argument("config_option")

    def get_config(self, config_option):
        mapping = {
            "siteconfig": SiteConfigurationSettings,
            "kic": KICConfigurationSettings,
            "zgw": ZGWConfigurationSettings,
            "digid_oidc": DigiDOIDCConfigurationSettings,
            "eherkenning_oidc": eHerkenningDOIDCConfigurationSettings,
        }
        return mapping[config_option]

    def get_detailed_info(self, config):
        ret = []
        for field, opts in config.fields.items():
            model_field = config.model._meta.get_field(field)
            part = []
            part.append(f"{'Variable':<20}{config.get_setting_name(field)}")
            part.append(f"{'Setting':<20}{str(model_field.verbose_name)}")
            part.append(f"{'Description':<20}{str(model_field.help_text)}")
            part.append(f"{'Possible values':<20}{opts['values']}")
            ret.append(part)
        return ret

    def write_file_from_template(self, template_path, template_variables, output_path):
        with open(template_path, "r") as template:
            template_str = template.read()
            template = Environment(loader=FileSystemLoader(TEMPLATE_DIR)).from_string(
                template_str
            )
            rendered = template.render(template_variables)

            with open(output_path, "w") as output:
                output.write(rendered)

    def handle(self, *args, **kwargs):
        config_option = kwargs["config_option"]
        if not config_option or config_option not in SUPPORTED_OPTIONS:
            return

        config = self.get_config(config_option)

        required_settings = [
            config.get_setting_name(field) for field in config.required_fields
        ]
        all_settings = [config.get_setting_name(field) for field in config.fields]
        detailed_info = self.get_detailed_info(config)
        template_variables = {
            "required_settings": required_settings,
            "all_settings": all_settings,
            "detailed_info": detailed_info,
        }

        template_path = TEMPLATE_DIR / f"{config_option}.rst.template"
        output_path = TARGET_DIR / f"{config_option}.rst"

        self.write_file_from_template(template_path, template_variables, output_path)
