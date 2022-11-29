from django.db.models import Q, QuerySet


class PlanQuerySet(QuerySet):
    def connected(self, user):
        return self.filter(Q(created_by=user) | Q(plan_contacts__id=user.id)).distinct()
