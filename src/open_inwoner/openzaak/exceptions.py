class NotificationAuthInvalid(Exception):
    pass


class NotificationAuthInvalidForClientID(NotificationAuthInvalid):
    def __init__(self, client_id):
        self.client_id = client_id
        super().__init__(f"notification invalid for client_id '{client_id}'")


class NotificationNotAcceptable(Exception):
    pass
