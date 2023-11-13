from datetime import date

from django.db import models

from dateutil.relativedelta import relativedelta
from ordered_model.models import OrderedModelQuerySet
from treebeard.mp_tree import MP_NodeQuerySet

from open_inwoner.accounts.models import User
from open_inwoner.openzaak.cases import fetch_cases, resolve_zaak_type


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

    def filter_for_user_with_zaken(self, user: User):
        """
        Returns the categories linked to ZaakTypen for which the user has Zaken.
        """
        if not getattr(user, "bsn", None):
            return self

        cases = fetch_cases(user.bsn)

        months_since_last_zaak_per_zaaktype = {}
        for case in cases:
            resolve_zaak_type(case)

            duration_since_start = relativedelta(date.today(), case.startdatum)
            if (
                case.zaaktype.identificatie not in months_since_last_zaak_per_zaaktype
                or months_since_last_zaak_per_zaaktype[case.zaaktype.identificatie]
                > duration_since_start.months
            ):
                months_since_last_zaak_per_zaaktype[
                    case.zaaktype.identificatie
                ] = duration_since_start.months

        zaaktype_ids = list(months_since_last_zaak_per_zaaktype.keys())

        qs = self.filter(zaaktypen__overlap=zaaktype_ids)

        pks = []
        for category in qs:
            if not category.relevante_zaakperiode:
                pks.append(category.pk)
                continue

            for identificatie in category.zaaktypen:
                if (
                    months_since_last_zaak_per_zaaktype[identificatie]
                    <= category.relevante_zaakperiode
                ):
                    pks.append(category.pk)
                    break

        return qs.filter(pk__in=pks)


class QuestionQueryset(OrderedModelQuerySet):
    def general(self):
        return self.filter(category__isnull=True, product__isnull=True)
