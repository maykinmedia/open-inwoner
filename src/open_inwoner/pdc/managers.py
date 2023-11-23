from datetime import date

from django.db import models

from dateutil.relativedelta import relativedelta
from ordered_model.models import OrderedModelQuerySet
from treebeard.mp_tree import MP_NodeQuerySet

from open_inwoner.accounts.models import User
from open_inwoner.openzaak.cases import fetch_cases, resolve_zaak_type
from open_inwoner.openzaak.models import ZaakTypeConfig


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
            if user.bsn:
                return self.filter(visible_for_citizens=True)
            elif user.kvk:
                return self.filter(visible_for_companies=True)
            return self.filter(visible_for_authenticated=True)
        return self.filter(visible_for_anonymous=True)

    def filter_for_user_with_zaken(self, user: User):
        """
        Returns the categories linked to ZaakTypen for which the user has Zaken.
        """
        if not getattr(user, "bsn", None):
            return self

        zaaktypen = ZaakTypeConfig.objects.all()
        url_to_identificatie_mapping = {
            url: zaaktype.identificatie
            for zaaktype in zaaktypen
            for url in zaaktype.urls
        }
        zaakperiode_mapping = {
            zaaktype.identificatie: zaaktype.relevante_zaakperiode
            for zaaktype in zaaktypen
        }

        cases = fetch_cases(user.bsn)

        months_since_last_zaak_per_zaaktype = {}
        for case in cases:
            # TODO This can occur if the import ZGW data is missing entries or if the
            # user has Zaken for zaaktypen with indicatie intern
            if case.zaaktype not in url_to_identificatie_mapping:
                continue

            zaaktype_identificatie = url_to_identificatie_mapping[case.zaaktype]

            duration_since_start = relativedelta(date.today(), case.startdatum)
            if (
                zaaktype_identificatie not in months_since_last_zaak_per_zaaktype
                or months_since_last_zaak_per_zaaktype[zaaktype_identificatie]
                > duration_since_start.months
            ):
                months_since_last_zaak_per_zaaktype[
                    zaaktype_identificatie
                ] = duration_since_start.months

        zaaktype_ids = list(months_since_last_zaak_per_zaaktype.keys())

        qs = self.filter(zaaktypen__overlap=zaaktype_ids)

        pks = []
        for category in qs:
            for identificatie in category.zaaktypen:
                relevante_zaakperiode = zaakperiode_mapping.get(identificatie)
                if not relevante_zaakperiode:
                    pks.append(category.pk)
                    continue

                if (
                    months_since_last_zaak_per_zaaktype[identificatie]
                    <= relevante_zaakperiode
                ):
                    pks.append(category.pk)
                    break

        return qs.filter(pk__in=pks)


class QuestionQueryset(OrderedModelQuerySet):
    def general(self):
        return self.filter(category__isnull=True, product__isnull=True)
