from itertools import groupby

from django.db.models import Q, query


class MessageQuerySet(query.QuerySet):
    def get_messages_between_users(self, me, other_user):
        return self.filter(
            Q(sender=me, receiver=other_user) | Q(sender=other_user, receiver=me)
        ).order_by("-created_on")
