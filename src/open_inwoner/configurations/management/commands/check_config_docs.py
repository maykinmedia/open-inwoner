from pathlib import Path

from django.conf import settings

from open_inwoner.configurations.bootstrap.registry import ConfigurationRegistry

from .generate_config_docs import ConfigDocBaseCommand

SUPPORTED_OPTIONS = ConfigurationRegistry.get_field_names()
SOURCE_DIR = Path(settings.BASE_DIR) / "docs" / "configuration"


class Command(ConfigDocBaseCommand):
    help = "Check that changes to the configuration setup classes are reflected in the documentation"

    def check_doc(self, config_option: str) -> None:
        source_path = SOURCE_DIR / f"{config_option}.rst"

        try:
            with open(source_path, "r") as file:
                config_content = file.read()
        except FileNotFoundError:
            self.stdout.write(
                "No documentation was found for {config}\n"
                "Did you forget to run generate_config_docs?\n\n".format(
                    config=self.get_config(config_option, class_name_only=True)
                )
            )
            raise
        else:
            # render new doc
            rendered_content = self.render_doc(config_option)

            if rendered_content != config_content:
                self.stdout.write(
                    "Class {config} has changes which are not reflected in the documentation ({source_path})\n"
                    "Did you forget to run generate_config_docs?\n\n".format(
                        config=self.get_config(config_option, class_name_only=True),
                        source_path=source_path,
                    )
                )
                raise ValueError("check_config_docs failed")

    def handle(self, *args, **kwargs) -> None:
        for option in SUPPORTED_OPTIONS:
            self.check_doc(option)
