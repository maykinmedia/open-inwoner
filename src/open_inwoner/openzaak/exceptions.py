class InvalidAuth(Exception):
    pass


class NoSubscriptionForClientID(InvalidAuth):
    def __init__(self, client_id):
        self.client_id = client_id
        super().__init__(f"no subscriptions for client_id '{client_id}'")


class InvalidAuthForClientID(InvalidAuth):
    def __init__(self, client_id):
        self.client_id = client_id
        super().__init__(f"secret invalid for subscription client_id'{client_id}'")
