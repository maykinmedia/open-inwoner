from django.utils.translation import gettext_lazy as _


class ErrorMessageMixin:
    custom_error_messages = {
        "required": _(
            "Het verplichte veld %s is niet (goed) ingevuld. Vul het veld in."
        )
    }

    def __init__(self, *args, **kwargs):
        user_added_messages = {}
        if "custom_error_messages" in kwargs:
            user_added_messages = kwargs.pop("custom_error_messages")
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            global_error_messages = {
                key: value
                for key, value in user_added_messages.items()
                if key not in self.fields
            }
            field_error_messages = user_added_messages.get(field_name, {})
            if (
                "required" not in global_error_messages
                and "required" not in field_error_messages
            ):
                required_message = (
                    self.custom_error_messages["required"] % f'"{field.label}"'
                )
            elif "required" in field_error_messages:
                required_message = user_added_messages[field_name]["required"]
            else:
                required_message = user_added_messages["required"]
            error_messages = {
                **global_error_messages,
                **field_error_messages,
                "required": required_message,
            }
            field.error_messages.update({**error_messages})
