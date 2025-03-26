KVK_BRANCH_SESSION_VARIABLE = "KVK_BRANCH_NUMBER"


def kvk_branch_selected_done(session) -> bool:
    return KVK_BRANCH_SESSION_VARIABLE in session
