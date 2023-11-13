from django.db import models

from ordered_model.models import OrderedModelQuerySet
from treebeard.mp_tree import MP_NodeQuerySet

from open_inwoner.accounts.models import User


class ProductQueryset(models.QuerySet):
    def published(self):
        return self.filter(published=True)

    def draft(self):
        return self.filter(published=False)

    def order_in_category(self):
        return self.order_by("categoryproduct__order")


class CategoryPublishedQueryset(MP_NodeQuerySet):
    def published(self):
        return self.filter(published=True)

    def draft(self):
        return self.filter(published=False)

    def visible_for_user(self, user: User):
        if user.is_authenticated:
            if getattr(user, "bsn", None):
                return self.filter(visible_for_citizens=True)
            elif getattr(user, "kvk", None):
                return self.filter(visible_for_companies=True)
            return self.filter(visible_for_authenticated=True)
        return self.filter(visible_for_anonymous=True)


class QuestionQueryset(OrderedModelQuerySet):
    def general(self):
        return self.filter(category__isnull=True, product__isnull=True)
