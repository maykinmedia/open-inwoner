import itertools
import pathlib

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template import loader
from django.utils.module_loading import import_string

from ..config_settings import ConfigSettings


class ConfigDocBase:
    """
    Base class encapsulating the functionality for generating + checking documentation.

    Defined independently of `BaseCommand` for more flexibility (the class could be
    used without running a Django management command).
    """

    @staticmethod
    def extract_unique_settings(settings: list[list[str]]) -> list[str]:
        """
        Flatten `settings` (a list of lists with settings) and remove dupes
        """
        unique_settings = set(itertools.chain.from_iterable(settings))
        return list(unique_settings)

    @staticmethod
    def add_additional_info(
        config_settings: ConfigSettings, result: list[list[str]]
    ) -> None:
        """Convenience/helper function to retrieve additional documentation info"""

        additional_info = config_settings.additional_info

        for key, value in additional_info.items():
            part = []
            part.append(f"{'Variable':<20}{value['variable']}")
            part.append(
                f"{'Description':<20}{value['description'] or 'No description'}"
            )
            part.append(
                f"{'Possible values':<20}"
                f"{value.get('possible_values') or 'No information available'}"
            )
            part.append(
                f"{'Default value':<20}{value.get('default_value') or 'No default'}"
            )
            result.append(part)

    def get_detailed_info(
        self,
        config_settings: ConfigSettings,
        related_config_settings: list[ConfigSettings],
    ) -> list[list[str]]:
        """
        Get information about the configuration settings:
            1. from model fields associated with the `ConfigSettings`
            2. from information provided manually in the `ConfigSettings`
            3. from information provided manually in the `ConfigSettings` of related
               configuration steps
        """
        result = []
        for field in config_settings.config_fields:
            part = []
            part.append(
                f"{'Variable':<20}{config_settings.get_config_variable(field.name)}"
            )
            part.append(f"{'Setting':<20}{field.verbose_name}")
            part.append(f"{'Description':<20}{field.description or 'No description'}")
            part.append(f"{'Possible values':<20}{field.field_description}")
            part.append(f"{'Default value':<20}{field.default_value}")
            result.append(part)

        self.add_additional_info(config_settings, result)

        for config_settings in related_config_settings:
            self.add_additional_info(config_settings, result)

        return result

    def format_display_name(self, display_name: str) -> str:
        """Surround title with '=' to display as heading in rst file"""

        heading_bar = "=" * len(display_name)
        display_name_formatted = f"{heading_bar}\n{display_name}\n{heading_bar}"
        return display_name_formatted

    def render_doc(self, config_settings: ConfigSettings, config_step) -> str:
        """
        Render a `ConfigSettings` documentation template with the following variables:
            1. enable_setting
            2. required_settings
            3. all_settings (required_settings + optional_settings + related settings)
            4. detailed_info
            5. title
            6. link (for crossreference across different files)
        """
        # 1.
        enable_setting = getattr(config_settings, "enable_setting", None)

        # 2.
        required_settings = [
            name for name in getattr(config_settings, "required_settings", [])
        ]

        # additional settings from related configuration steps to embed
        # the documentation of several steps into one
        related_config_settings = [
            config for config in getattr(config_settings, "related_config_settings", [])
        ]
        required_settings_related = self.extract_unique_settings(
            [config.required_settings for config in related_config_settings]
        )
        optional_settings_related = self.extract_unique_settings(
            [config.optional_settings for config in related_config_settings]
        )

        required_settings.extend(required_settings_related)
        required_settings.sort()

        # 3.
        all_settings = [
            setting
            for setting in required_settings
            + config_settings.optional_settings
            + optional_settings_related
        ]
        all_settings.sort()

        # 4.
        detailed_info = self.get_detailed_info(
            config_settings,
            related_config_settings,
        )
        detailed_info.sort()

        # 5.
        title = self.format_display_name(config_step.verbose_name)

        template_variables = {
            "enable_setting": enable_setting,
            "required_settings": required_settings,
            "all_settings": all_settings,
            "detailed_info": detailed_info,
            "link": f".. _{config_settings.file_name}:",
            "title": title,
        }

        template = loader.get_template(settings.DJANGO_SETUP_CONFIG_TEMPLATE)
        rendered = template.render(template_variables)

        return rendered


class Command(ConfigDocBase, BaseCommand):
    help = "Generate documentation for configuration setup steps"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help=("Check that the documentation is up-to-date without creating it"),
        )

    def content_is_up_to_date(self, rendered_content: str, doc_path: str) -> bool:
        """
        Check that documentation at `doc_path` exists and that its content matches
        that of `rendered_content`
        """
        try:
            with open(doc_path, "r") as file:
                file_content = file.read()
        except FileNotFoundError:
            return False

        if not file_content == rendered_content:
            return False

        return True

    def handle(self, *args, **kwargs) -> None:
        dry_run = kwargs["dry_run"]

        target_dir = settings.DJANGO_SETUP_CONFIG_DOC_PATH

        # create directory for docs if it doesn't exist
        pathlib.Path(target_dir).mkdir(parents=True, exist_ok=True)

        for config_string in settings.SETUP_CONFIGURATION_STEPS:
            config_step = import_string(config_string)

            config_settings = getattr(config_step, "config_settings", None)
            if not config_settings or not config_settings.independent:
                continue

            doc_path = f"{target_dir}/{config_settings.file_name}.rst"
            rendered_content = self.render_doc(config_settings, config_step)

            up_to_date = self.content_is_up_to_date(rendered_content, doc_path)

            if not up_to_date and not dry_run:
                with open(doc_path, "w+") as output:
                    output.write(rendered_content)
            elif not up_to_date:
                raise ValueError(
                    f"The documentation for {config_step} is not up-to-date"
                )
