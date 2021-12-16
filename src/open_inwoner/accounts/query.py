from collections import OrderedDict
from datetime import date
from itertools import groupby
from typing import Dict

from django.db.models import Q, query


class MessageQuerySet(query.QuerySet):
    def get_messages_between_users(self, me, other_user) -> Dict[date, list]:
        """grouped by date"""
        messages = list(
            self.filter(
                Q(sender=me, receiver=other_user) | Q(sender=other_user, receiver=me)
            ).order_by("created_on")
        )

        groups = OrderedDict()

        for create_date, group in groupby(messages, lambda x: x.created_on.date()):
            groups[create_date] = list(group)

        return groups

    def get_conversations_for_user(self, me):
        """returns dict {user: last_message}"""
        # TODO refactor to be executed in DB
        conversations = OrderedDict()

        sent_messages = self.filter(sender=me).order_by("receiver", "-created_on")
        for user, group in groupby(sent_messages, lambda x: x.receiver):
            conversations[user] = next(group)

        received_messages = self.filter(receiver=me).order_by("sender", "-created_on")
        for user, group in groupby(received_messages, lambda x: x.sender):
            received_message = next(group)

            if user not in conversations:
                conversations[user] = received_message
            else:
                sent_message = conversations.get(user)
                latest_message = (
                    received_message
                    if received_message.created_on >= sent_message.created_on
                    else sent_message
                )
                conversations[user] = latest_message

        return conversations
