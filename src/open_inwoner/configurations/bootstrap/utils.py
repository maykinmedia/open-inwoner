BOLD = "\033[1m"
NORMAL = "\033[0m"


def convert_setting_to_model_field_name(setting: str, namespace: str) -> str:
    return setting.split(f"{namespace}_", 1)[1].lower()


def print_form_errors(config_step, form):
    print(
        f"\n{BOLD}There are problems with the settings for {config_step.verbose_name}:\n{NORMAL}"
    )
    for field, errors in form.errors.items():
        print(f"{field}: {'; '.join(errors)}\n")
