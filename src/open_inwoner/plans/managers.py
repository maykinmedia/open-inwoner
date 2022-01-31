from django.db.models import Q, QuerySet


class PlanQuerySet(QuerySet):
    def connected(self, user):
        return self.filter(
            Q(created_by=user) | Q(contacts__contact_user=user)
        ).distinct()

    def shared(self, user):
        return self.filter(contacts__contact_user=user).distinct()
