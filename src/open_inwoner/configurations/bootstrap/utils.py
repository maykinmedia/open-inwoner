def generate_api_fields_from_template(api_name: str) -> dict[str, str]:
    name = api_name.split("_")[0].capitalize()

    return {
        f"{api_name}_root": {
            "verbose_name": f"Root URL of the {name} API",
            "values": "string (URL)",
        },
        f"{api_name}_client_id": {
            "verbose_name": f"Client ID for the {name} API",
            "values": "string",
        },
        f"{api_name}_client_secret": {
            "verbose_name": f"Secret for the {name} API",
            "values": "string",
        },
    }
