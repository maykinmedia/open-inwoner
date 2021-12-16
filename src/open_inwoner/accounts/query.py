from collections import OrderedDict
from itertools import groupby
from django.db.models import Case, When, F, Q, Value, query
from django.db.models.functions import Concat
from open_inwoner.components.types.messagetype import MessageType


class MessageQuerySet(query.QuerySet):
    def get_messages_between_users(self, me, other_user) -> 'MessageQuerySet':
        """grouped by date"""
        return self.filter(
            Q(sender=me, receiver=other_user) | Q(sender=other_user, receiver=me)
        ).order_by("created_on")

    def get_conversations_for_user(self, me):
        conversations = self.filter(
            Q(sender=me) | Q(receiver=me)
        ).annotate(
            other_user=Case(
                When(
                    sender=me,
                    then=Concat(
                        F('receiver__first_name'),
                        Value(' '),
                        F('receiver__last_name'),
                    )
                ),
                When(
                    receiver=me,
                    then=Concat(
                        F('sender__first_name'),
                        Value(' '),
                        F('sender__last_name'),
                    ),
                ),
            )
        ).distinct(
            "other_user"
        )

        return conversations

    def as_message_type(self) -> list[MessageType]:
        """
        Returns all messages as MessageType.
        """
        message_types = []
        for message in self:
            message_type = message.as_message_type()
            message_types.append(message_type)

        return message_types
