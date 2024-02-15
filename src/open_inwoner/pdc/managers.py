from datetime import date
from typing import List

from django.db import models

from dateutil.relativedelta import relativedelta
from ordered_model.models import OrderedModelQuerySet
from treebeard.mp_tree import MP_NodeQuerySet

from open_inwoner.accounts.models import User
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.openzaak.api_models import Zaak
from open_inwoner.openzaak.clients import build_client
from open_inwoner.openzaak.models import ZaakTypeConfig
from open_inwoner.openzaak.utils import get_fetch_parameters


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

        config = SiteConfiguration.get_solo()
        if config.hide_categories_from_anonymous_users:
            return self.none()
        return self.filter(visible_for_anonymous=True)

    def filter_by_zaken_for_request(self, request):
        """
        Returns the categories linked to ZaakTypen for which the request's user has Zaken.
        """
        if not request.user.bsn and not request.user.kvk:
            return self

        client = build_client("zaak")
        if client is None:
            return self.none()

        cases = client.fetch_cases(**get_fetch_parameters(request))

        return self.filter_by_zaken(cases)

    def filter_by_zaken(self, cases: List[Zaak]):
        """
        Returns the categories linked to ZaakTypen matching with the specified Zaken.
        """
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
                if identificatie not in months_since_last_zaak_per_zaaktype:
                    continue
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
