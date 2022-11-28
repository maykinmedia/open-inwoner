from django.db import models

from ordered_model.models import OrderedModelQuerySet
from treebeard.mp_tree import MP_NodeQuerySet


class PublishedQueryset(models.QuerySet):
    def published(self):
        return self.filter(published=True)

    def draft(self):
        return self.filter(published=False)


class CategoryPublishedQueryset(MP_NodeQuerySet):
    def published(self):
        return self.filter(published=True)

    def draft(self):
        return self.filter(published=False)


class QuestionQueryset(OrderedModelQuerySet):
    def general(self):
        return self.filter(category__isnull=True, product__isnull=True)
