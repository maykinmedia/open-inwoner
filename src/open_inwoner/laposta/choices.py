from .api_models import LapostaList


def get_list_choices(lists: list[LapostaList]) -> list[tuple[str, tuple[str, str]]]:
    return [
        (laposta_list.list_id, (laposta_list.name, laposta_list.remarks))
        for laposta_list in lists
        if laposta_list.name
    ]
