from django.db.models import QuerySet


class PublishedQueryset(QuerySet):
    def published(self):
        return self.filter(published=True)

    def draft(self):
        return self.filter(published=False)
