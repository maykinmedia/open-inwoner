from typing import Optional

KVK_BRANCH_SESSION_VARIABLE = "KVK_BRANCH_NUMBER"


def kvk_branch_selected_done(session) -> bool:
    return KVK_BRANCH_SESSION_VARIABLE in session


def get_kvk_branch_number(session) -> Optional[str]:
    return session.get(KVK_BRANCH_SESSION_VARIABLE)
