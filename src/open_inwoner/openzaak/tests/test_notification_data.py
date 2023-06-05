from typing import List, Optional

from zgw_consumers.api_models.constants import (
    RolOmschrijving,
    RolTypes,
    VertrouwelijkheidsAanduidingen,
)
from zgw_consumers.constants import APITypes
from zgw_consumers.test import generate_oas_component, mock_service_oas_get

from open_inwoner.accounts.tests.factories import DigidUserFactory
from open_inwoner.openzaak.tests.factories import (
    NotificationFactory,
    ServiceFactory,
    ZaakTypeConfigFactory,
    ZaakTypeInformatieObjectTypeConfigFactory,
)
from open_inwoner.utils.test import paginated_response

from ..models import OpenZaakConfig
from .shared import CATALOGI_ROOT, DOCUMENTEN_ROOT, ZAKEN_ROOT


class MockAPIData:
    """
    initializes isolated and valid data for a complete mock-request API flow,
        allows to manipulate data per test to break it,
        and still get dry/readable access to the data for assertions

    # usage:

    data = MockAPIData()

    # change some resources
    data.zaak["some_field"] = "a different value"

    # install to your @requests_mock.Mocker()
    data.install_mocks(m)

    # install but return 404 for some resource
    data.install_mocks(m, res404=["zaak"])

    # also:

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        MockAPIData.setUpServices()

    """

    def __init__(self):
        self.user_initiator = DigidUserFactory(
            bsn="100000001",
            email="initiator@example.com",
        )
        self.zaak_type = generate_oas_component(
            "ztc",
            "schemas/ZaakType",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            url=f"{CATALOGI_ROOT}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            catalogus=f"{CATALOGI_ROOT}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            identificatie="My Zaaktype",
            indicatieInternOfExtern="extern",
            omschrijving="My Zaaktype omschrijving",
        )
        self.status_type_initial = generate_oas_component(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/aaaaaaaa-aaaa-aaaa-aaaa-111111111111",
            zaaktype=self.zaak_type["url"],
            informeren=True,
            volgnummer=1,
            omschrijving="initial",
            isEindStatus=False,
        )
        self.status_type_final = generate_oas_component(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/aaaaaaaa-aaaa-aaaa-aaaa-222222222222",
            zaaktype=self.zaak_type["url"],
            informeren=True,
            volgnummer=2,
            omschrijving="final",
            isEindStatus=True,
        )
        self.zaak = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            zaaktype=self.zaak_type["url"],
            status=f"{ZAKEN_ROOT}statussen/aaaaaaaa-aaaa-aaaa-aaaa-222222222222",
            resultaat=f"{ZAKEN_ROOT}resultaten/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.status_initial = generate_oas_component(
            "zrc",
            "schemas/Status",
            url=f"{ZAKEN_ROOT}statussen/aaaaaaaa-aaaa-aaaa-aaaa-111111111111",
            zaak=self.zaak["url"],
            statustype=self.status_type_initial["url"],
        )
        self.status_final = generate_oas_component(
            "zrc",
            "schemas/Status",
            url=f"{ZAKEN_ROOT}statussen/aaaaaaaa-aaaa-aaaa-aaaa-222222222222",
            zaak=self.zaak["url"],
            statustype=self.status_type_final["url"],
        )

        self.informatie_object = generate_oas_component(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            url=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/aaaaaaaa-0001-bbbb-aaaa-aaaaaaaaaaaa",
            informatieobjecttype=f"{CATALOGI_ROOT}informatieobjecttypen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            status="definitief",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.zaak_informatie_object = generate_oas_component(
            "zrc",
            "schemas/ZaakInformatieObject",
            url=f"{ZAKEN_ROOT}zaakinformatieobjecten/aaaaaaaa-0001-aaaa-aaaa-aaaaaaaaaaaa",
            informatieobject=self.informatie_object["url"],
            zaak=self.zaak["url"],
        )

        self.role_initiator = generate_oas_component(
            "zrc",
            "schemas/Rol",
            url=f"{ZAKEN_ROOT}rollen/aaaaaaaa-0001-aaaa-aaaa-aaaaaaaaaaaa",
            omschrijvingGeneriek=RolOmschrijving.initiator,
            betrokkeneType=RolTypes.natuurlijk_persoon,
            betrokkeneIdentificatie={
                "inpBsn": self.user_initiator.bsn,
            },
        )

        self.case_roles = [self.role_initiator]
        self.status_history = [self.status_initial, self.status_final]

        self.status_notification = NotificationFactory(
            resource="status",
            actie="update",
            resource_url=self.status_final["url"],
            hoofd_object=self.zaak["url"],
        )
        self.zio_notification = NotificationFactory(
            resource="zaakinformatieobject",
            actie="create",
            resource_url=self.zaak_informatie_object["url"],
            hoofd_object=self.zaak["url"],
        )

    def setUpOASMocks(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        mock_service_oas_get(m, DOCUMENTEN_ROOT, "drc")

    def install_mocks(self, m, *, res404: Optional[List[str]] = None) -> "MockAPIData":
        self.setUpOASMocks(m)
        if res404 is None:
            res404 = []
        for attr in res404:
            if not hasattr(self, attr):
                raise Exception("configuration error")

        if "case_roles" in res404:
            m.get(f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}", status_code=404)
        else:
            m.get(
                f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
                json=paginated_response(self.case_roles),
            )

        if "status_history" in res404:
            m.get(f"{ZAKEN_ROOT}statussen?zaak={self.zaak['url']}", status_code=404)
        else:
            m.get(
                f"{ZAKEN_ROOT}statussen?zaak={self.zaak['url']}",
                json=paginated_response(self.status_history),
            )

        for resource_attr in [
            "zaak",
            "zaak_type",
            "status_initial",
            "status_final",
            "status_type_initial",
            "status_type_final",
            "status_type_final",
            "informatie_object",
            "zaak_informatie_object",
        ]:
            resource = getattr(self, resource_attr)
            if resource_attr in res404:
                m.get(resource["url"], status_code=404)
            else:
                m.get(resource["url"], json=resource)

        return self

    @classmethod
    def setUpServices(cls):
        # openzaak config
        config = OpenZaakConfig.get_solo()
        config.zaak_service = ServiceFactory(api_root=ZAKEN_ROOT, api_type=APITypes.zrc)
        config.catalogi_service = ServiceFactory(
            api_root=CATALOGI_ROOT, api_type=APITypes.ztc
        )
        config.document_service = ServiceFactory(
            api_root=DOCUMENTEN_ROOT, api_type=APITypes.drc
        )
        config.zaak_max_confidentiality = VertrouwelijkheidsAanduidingen.openbaar
        config.save()
