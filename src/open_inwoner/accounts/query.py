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
