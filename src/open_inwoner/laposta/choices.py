from .api_models import LapostaList


def get_list_choices(lists: list[LapostaList]) -> list[tuple[str, str]]:
    return [
        (laposta_list.list_id, laposta_list.name)
        for laposta_list in lists
        if laposta_list.name
    ]


def get_list_remarks_mapping(lists: list[LapostaList]) -> dict[str, str]:
    return {laposta_list.list_id: laposta_list.remarks for laposta_list in lists}
