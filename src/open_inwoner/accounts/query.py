from django.db.models import Q, query

from open_inwoner.components.types.messagetype import MessageType


class MessageQuerySet(query.QuerySet):

    def get_conversations_for_user(self, me):
        # UGH!
        queryset = self.raw(
            f'SELECT * FROM (SELECT DISTINCT ON (other_user) other_user, * FROM (SELECT CASE WHEN sender_id={me.pk} THEN receiver_id WHEN receiver_id={me.pk} THEN sender_id END AS other_user, * FROM accounts_message WHERE sender_id=1 OR receiver_id=1 GROUP BY other_user, id ORDER BY created_on DESC) as q1) as q2 ORDER BY created_on DESC'
        )
        return queryset

    def get_messages_between_users(self, me, other_user) -> 'MessageQuerySet':
        """grouped by date"""
        return self.filter(
            Q(sender=me, receiver=other_user) | Q(sender=other_user, receiver=me)
        ).select_related('sender', 'receiver', ).order_by("created_on")

    def as_message_type(self) -> list[MessageType]:
        """
        Returns all messages as MessageType.
        """
        message_types = []
        for message in self:
            message_type = message.as_message_type()
            message_types.append(message_type)

        return message_types
