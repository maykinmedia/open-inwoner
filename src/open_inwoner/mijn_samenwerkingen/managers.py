from django.db.models import QuerySet


class PlanQuerySet(QuerySet):
    def connected(self, user):
        return self.filter(plan_contacts=user)
