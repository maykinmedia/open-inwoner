from django.db.models import Q, QuerySet


class PlanQuerySet(QuerySet):
    def connected(self, user):
        return self.filter(Q(created_by=user) | Q(plan_contacts__id=user.id)).distinct()

    def shared(self, user):
        return self.filter(
            Q(contacts__contact_user=user) | Q(contacts__created_by=user)
        ).distinct()
