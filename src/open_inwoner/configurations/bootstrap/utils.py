def convert_setting_to_model_field_name(setting: str, namespace: str) -> str:
    return setting.split(f"{namespace}_", 1)[1].lower()
