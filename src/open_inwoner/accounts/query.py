from django.db.models import Q
from django.db.models.query import QuerySet, RawQuerySet

from open_inwoner.components.types.messagetype import MessageType


class MessageQuerySet(QuerySet):
    def get_conversations_for_user(self, me: 'User') -> RawQuerySet:
        """
        I apologize;

        Summary:

            Returns every conversation involving me, newest first.

        Details:

            A conversation is a Message, annotated with:
                - other_user_id
                - other_user_email
                - other_user_first_name
                - other_user_last_name

            other_user_id matches the value of either sender or receiver field,
            (based on which one  does not match me.pk).

            Conversations should be the newest messages with other_user_id.

            Conversations should be unique/distinct by other_user_id.

        PostgreSQL issues:

            The typical way of performing this query would be using annotation and possibly other (advanced) ORM usage,
            however this would most likely result in a combination of some or all of:

             - DISTINCT ON (other_user)
             - GROUP_BY (other_user)
             - ORDER BY (created_on)

            Which is not supported in PostgreSQL, and might trigger errors like:

                ERROR:  SELECT DISTINCT ON expressions must match initial ORDER BY expressions

            I've tried various approaches to work around this issue (keeping pagination support, performance and lazy
            loading in mind). But in the end came up with a raw query.
        """

        # UGH!
        queryset = self.raw(
            "SELECT q1.*, "
            "accounts_user.first_name as other_user_first_name, "
            "accounts_user.last_name as other_user_last_name, "
            "accounts_user.email as other_user_email "
            "FROM ("
            "   SELECT DISTINCT ON (other_user_id) "
            "   CASE "
            "       WHEN sender_id = %s THEN receiver_id "
            "       WHEN receiver_id = %s THEN sender_id "
            "   END "
            "   AS other_user_id, * "
            "   FROM accounts_message "
            "   WHERE sender_id = %s OR receiver_id = %s "
            "   GROUP BY other_user_id, id "
            "   ORDER BY other_user_id, created_on DESC"
            ") as q1 "
            "INNER JOIN accounts_user ON q1.other_user_id=accounts_user.id "
            "ORDER BY created_on DESC"
            , (me.pk, me.pk, me.pk, me.pk))

        return queryset

    def get_messages_between_users(self, me, other_user) -> QuerySet:
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
