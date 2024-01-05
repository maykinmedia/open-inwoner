from typing import Optional

KVK_BRANCH_SESSION_VARIABLE = "KVK_BRANCH_NUMBER"


def get_kvk_branch_number(session) -> Optional[str]:
    return session.get(KVK_BRANCH_SESSION_VARIABLE)
