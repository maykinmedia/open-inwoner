from zgw_consumers.api_models.constants import (
    RolOmschrijving,
    RolTypes,
    VertrouwelijkheidsAanduidingen,
)

from open_inwoner.accounts.tests.factories import (
    DigidUserFactory,
    eHerkenningUserFactory,
)
from open_inwoner.openzaak.tests.factories import (
    NotificationFactory,
    ZGWApiGroupConfigFactory,
)
from open_inwoner.utils.test import paginated_response

from .helpers import generate_oas_component_cached
from .shared import (
    ANOTHER_CATALOGI_ROOT,
    ANOTHER_DOCUMENTEN_ROOT,
    ANOTHER_ZAKEN_ROOT,
    CATALOGI_ROOT,
    DOCUMENTEN_ROOT,
    ZAKEN_ROOT,
)


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
        self.eherkenning_user_initiator = eHerkenningUserFactory(
            kvk="12345678",
            rsin="000000000",
            email="initiator_kvk@example.com",
        )
        self.zaak_type = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            url=f"{CATALOGI_ROOT}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            catalogus=f"{CATALOGI_ROOT}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            identificatie="My Zaaktype",
            indicatieInternOfExtern="extern",
            omschrijving="My Zaaktype omschrijving",
        )
        self.status_type_initial = generate_oas_component_cached(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/aaaaaaaa-aaaa-aaaa-aaaa-111111111111",
            zaaktype=self.zaak_type["url"],
            informeren=True,
            volgnummer=1,
            omschrijving="initial",
            statustekst="",
            isEindStatus=False,
        )
        self.status_type_final = generate_oas_component_cached(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/aaaaaaaa-aaaa-aaaa-aaaa-222222222222",
            zaaktype=self.zaak_type["url"],
            informeren=True,
            volgnummer=2,
            omschrijving="final",
            statustekst="status_type_final_statustekst",
            isEindStatus=True,
        )
        self.zaak = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            zaaktype=self.zaak_type["url"],
            status=f"{ZAKEN_ROOT}statussen/aaaaaaaa-aaaa-aaaa-aaaa-222222222222",
            resultaat=f"{ZAKEN_ROOT}resultaten/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.zaak2 = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            zaaktype=self.zaak_type["url"],
            status=f"{ZAKEN_ROOT}statussen/aaaaaaaa-aaaa-aaaa-aaaa-222222222222",
            resultaat=f"{ZAKEN_ROOT}resultaten/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.status_initial = generate_oas_component_cached(
            "zrc",
            "schemas/Status",
            url=f"{ZAKEN_ROOT}statussen/aaaaaaaa-aaaa-aaaa-aaaa-111111111111",
            zaak=self.zaak["url"],
            statustype=self.status_type_initial["url"],
        )
        self.status_final = generate_oas_component_cached(
            "zrc",
            "schemas/Status",
            url=f"{ZAKEN_ROOT}statussen/aaaaaaaa-aaaa-aaaa-aaaa-222222222222",
            zaak=self.zaak["url"],
            statustype=self.status_type_final["url"],
        )

        self.informatie_object = generate_oas_component_cached(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            url=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/aaaaaaaa-0001-bbbb-aaaa-aaaaaaaaaaaa",
            informatieobjecttype=f"{CATALOGI_ROOT}informatieobjecttypen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            status="definitief",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.zaak_informatie_object = generate_oas_component_cached(
            "zrc",
            "schemas/ZaakInformatieObject",
            url=f"{ZAKEN_ROOT}zaakinformatieobjecten/aaaaaaaa-0001-aaaa-aaaa-aaaaaaaaaaaa",
            informatieobject=self.informatie_object["url"],
            zaak=self.zaak["url"],
        )
        self.zaak_informatie_object2 = generate_oas_component_cached(
            "zrc",
            "schemas/ZaakInformatieObject",
            url=f"{ZAKEN_ROOT}zaakinformatieobjecten/aaaaaaaa-0002-aaaa-aaaa-aaaaaaaaaaaa",
            informatieobject=self.informatie_object["url"],
            zaak=self.zaak2["url"],
        )

        self.informatie_object_extra = generate_oas_component_cached(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            url=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/aaaaaaaa-0002-bbbb-aaaa-aaaaaaaaaaaa",
            informatieobjecttype=f"{CATALOGI_ROOT}informatieobjecttypen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            status="definitief",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.zaak_informatie_object_extra = generate_oas_component_cached(
            "zrc",
            "schemas/ZaakInformatieObject",
            url=f"{ZAKEN_ROOT}zaakinformatieobjecten/aaaaaaaa-0003-aaaa-aaaa-aaaaaaaaaaaa",
            informatieobject=self.informatie_object_extra["url"],
            zaak=self.zaak["url"],
        )

        self.role_initiator = generate_oas_component_cached(
            "zrc",
            "schemas/Rol",
            url=f"{ZAKEN_ROOT}rollen/aaaaaaaa-0001-aaaa-aaaa-aaaaaaaaaaaa",
            omschrijvingGeneriek=RolOmschrijving.initiator,
            betrokkeneType=RolTypes.natuurlijk_persoon,
            betrokkeneIdentificatie={
                "inpBsn": self.user_initiator.bsn,
            },
        )
        self.eherkenning_role_initiator = generate_oas_component_cached(
            "zrc",
            "schemas/Rol",
            url=f"{ZAKEN_ROOT}rollen/aaaaaaaa-0002-aaaa-aaaa-aaaaaaaaaaaa",
            omschrijvingGeneriek=RolOmschrijving.initiator,
            betrokkeneType=RolTypes.niet_natuurlijk_persoon,
            betrokkeneIdentificatie={
                "innNnpId": self.eherkenning_user_initiator.kvk,
            },
        )
        self.eherkenning_role_initiator2 = generate_oas_component_cached(
            "zrc",
            "schemas/Rol",
            url=f"{ZAKEN_ROOT}rollen/aaaaaaaa-0003-aaaa-aaaa-aaaaaaaaaaaa",
            omschrijvingGeneriek=RolOmschrijving.initiator,
            betrokkeneType=RolTypes.niet_natuurlijk_persoon,
            betrokkeneIdentificatie={
                "innNnpId": self.eherkenning_user_initiator.rsin,
            },
        )

        self.case_roles = [self.role_initiator]
        self.eherkenning_case_roles = [
            self.eherkenning_role_initiator,
            self.eherkenning_role_initiator2,
        ]
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
        self.zio_notification2 = NotificationFactory(
            resource="zaakinformatieobject",
            actie="create",
            resource_url=self.zaak_informatie_object2["url"],
            hoofd_object=self.zaak2["url"],
        )

    def install_mocks(self, m, *, res404: list[str] | None = None):
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
            m.get(
                f"{ZAKEN_ROOT}rollen?zaak={self.zaak2['url']}",
                json=paginated_response(self.eherkenning_case_roles),
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
            "zaak2",
            "zaak_type",
            "status_initial",
            "status_final",
            "status_type_initial",
            "status_type_final",
            "status_type_final",
            "informatie_object",
            "zaak_informatie_object",
            "zaak_informatie_object2",
            "informatie_object_extra",
            "zaak_informatie_object_extra",
        ]:
            resource = getattr(self, resource_attr)
            if resource_attr in res404:
                m.get(resource["url"], status_code=404)
            else:
                m.get(resource["url"], json=resource)

        return self

    @classmethod
    def setUpServices(cls):
        cls.api_group = ZGWApiGroupConfigFactory(
            ztc_service__api_root=CATALOGI_ROOT,
            zrc_service__api_root=ZAKEN_ROOT,
            drc_service__api_root=DOCUMENTEN_ROOT,
            form_service=None,
        )


class MockAPIDataAlt:
    """
    Additional API data for testing multiple ZGW backends.

    The set of mocks is a replica of `MockAPIData` but with different API roots
    """

    def __init__(self):
        self.user_initiator_alt = DigidUserFactory(
            bsn="200000002",
            email="initiator_alt@example.com",
        )
        self.eherkenning_user_initiator_alt = eHerkenningUserFactory(
            kvk="87654321",
            rsin="000000000",
            email="initiator_alt_kvk@example.com",
        )
        self.zaak_type_alt = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            uuid="22fd7613-3c9d-4507-a0b1-32c503488988",
            url=f"{ANOTHER_CATALOGI_ROOT}zaaktype/22fd7613-3c9d-4507-a0b1-32c503488988",
            catalogus=f"{ANOTHER_CATALOGI_ROOT}catalogussen/22fd7613-3c9d-4507-a0b1-32c503488988",
            identificatie="My Zaaktype",
            indicatieInternOfExtern="extern",
            omschrijving="My Zaaktype omschrijving",
        )
        self.status_type_initial_alt = generate_oas_component_cached(
            "ztc",
            "schemas/StatusType",
            url=f"{ANOTHER_CATALOGI_ROOT}statustypen/aaaaaaaa-aaaa-aaaa-aaaa-111111111111",
            zaaktype=self.zaak_type_alt["url"],
            informeren=True,
            volgnummer=1,
            omschrijving="initial",
            statustekst="",
            isEindStatus=False,
        )
        self.status_type_final_alt = generate_oas_component_cached(
            "ztc",
            "schemas/StatusType",
            url=f"{ANOTHER_CATALOGI_ROOT}statustypen/aaaaaaaa-aaaa-aaaa-aaaa-222222222222",
            zaaktype=self.zaak_type_alt["url"],
            informeren=True,
            volgnummer=2,
            omschrijving="final",
            statustekst="status_type_final_statustekst",
            isEindStatus=True,
        )
        self.zaak_alt = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            url=f"{ANOTHER_ZAKEN_ROOT}zaken/22fd7613-3c9d-4507-a0b1-32c503488988",
            zaaktype=self.zaak_type_alt["url"],
            status=f"{ANOTHER_ZAKEN_ROOT}statussen/22fd7613-3c9d-4507-a0b1-32c503488988",
            resultaat=f"{ANOTHER_ZAKEN_ROOT}resultaten/22fd7613-3c9d-4507-a0b1-32c503488988",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.zaak2_alt = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            url=f"{ANOTHER_ZAKEN_ROOT}zaken/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            zaaktype=self.zaak_type_alt["url"],
            status=f"{ANOTHER_ZAKEN_ROOT}statussen/aaaaaaaa-aaaa-aaaa-aaaa-222222222222",
            resultaat=f"{ANOTHER_ZAKEN_ROOT}resultaten/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.status_initial_alt = generate_oas_component_cached(
            "zrc",
            "schemas/Status",
            url=f"{ANOTHER_ZAKEN_ROOT}statussen/22fd7613-3c9d-4507-a0b1-32c503488988",
            zaak=self.zaak_alt["url"],
            statustype=self.status_type_initial_alt["url"],
        )
        self.status_final_alt = generate_oas_component_cached(
            "zrc",
            "schemas/Status",
            url=f"{ANOTHER_ZAKEN_ROOT}statussen/22fd7613-3c9d-4507-a0b1-32c503488988",
            zaak=self.zaak_alt["url"],
            statustype=self.status_type_final_alt["url"],
        )

        self.informatie_object_alt = generate_oas_component_cached(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            url=f"{ANOTHER_DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/aaaaaaaa-0001-bbbb-aaaa-aaaaaaaaaaaa",
            informatieobjecttype=f"{ANOTHER_CATALOGI_ROOT}informatieobjecttypen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            status="definitief",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.zaak_informatie_object_alt = generate_oas_component_cached(
            "zrc",
            "schemas/ZaakInformatieObject",
            url=f"{ANOTHER_ZAKEN_ROOT}zaakinformatieobjecten/aaaaaaaa-0001-aaaa-aaaa-aaaaaaaaaaaa",
            informatieobject=self.informatie_object_alt["url"],
            zaak=self.zaak_alt["url"],
        )
        self.zaak_informatie_object2_alt = generate_oas_component_cached(
            "zrc",
            "schemas/ZaakInformatieObject",
            url=f"{ANOTHER_ZAKEN_ROOT}zaakinformatieobjecten/aaaaaaaa-0002-aaaa-aaaa-aaaaaaaaaaaa",
            informatieobject=self.informatie_object_alt["url"],
            zaak=self.zaak2_alt["url"],
        )
        self.informatie_object_extra_alt = generate_oas_component_cached(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            url=f"{ANOTHER_DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/aaaaaaaa-0002-bbbb-aaaa-aaaaaaaaaaaa",
            informatieobjecttype=f"{ANOTHER_CATALOGI_ROOT}informatieobjecttypen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            status="definitief",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.zaak_informatie_object_extra_alt = generate_oas_component_cached(
            "zrc",
            "schemas/ZaakInformatieObject",
            url=f"{ANOTHER_ZAKEN_ROOT}zaakinformatieobjecten/aaaaaaaa-0003-aaaa-aaaa-aaaaaaaaaaaa",
            informatieobject=self.informatie_object_extra_alt["url"],
            zaak=self.zaak_alt["url"],
        )

        self.role_initiator_alt = generate_oas_component_cached(
            "zrc",
            "schemas/Rol",
            url=f"{ANOTHER_ZAKEN_ROOT}rollen/aaaaaaaa-0001-aaaa-aaaa-aaaaaaaaaaaa",
            omschrijvingGeneriek=RolOmschrijving.initiator,
            betrokkeneType=RolTypes.natuurlijk_persoon,
            betrokkeneIdentificatie={
                "inpBsn": self.user_initiator_alt.bsn,
            },
        )
        self.eherkenning_role_initiator_alt = generate_oas_component_cached(
            "zrc",
            "schemas/Rol",
            url=f"{ANOTHER_ZAKEN_ROOT}rollen/aaaaaaaa-0002-aaaa-aaaa-aaaaaaaaaaaa",
            omschrijvingGeneriek=RolOmschrijving.initiator,
            betrokkeneType=RolTypes.niet_natuurlijk_persoon,
            betrokkeneIdentificatie={
                "innNnpId": self.eherkenning_user_initiator_alt.kvk,
            },
        )
        self.eherkenning_role_initiator2_alt = generate_oas_component_cached(
            "zrc",
            "schemas/Rol",
            url=f"{ANOTHER_ZAKEN_ROOT}rollen/aaaaaaaa-0003-aaaa-aaaa-aaaaaaaaaaaa",
            omschrijvingGeneriek=RolOmschrijving.initiator,
            betrokkeneType=RolTypes.niet_natuurlijk_persoon,
            betrokkeneIdentificatie={
                "innNnpId": self.eherkenning_user_initiator_alt.rsin,
            },
        )

        self.case_roles_alt = [self.role_initiator_alt]
        self.eherkenning_case_roles_alt = [
            self.eherkenning_role_initiator_alt,
            self.eherkenning_role_initiator2_alt,
        ]
        self.status_history_alt = [self.status_initial_alt, self.status_final_alt]

        self.status_notification_alt = NotificationFactory(
            resource="status",
            actie="update",
            resource_url=self.status_final_alt["url"],
            hoofd_object=self.zaak_alt["url"],
        )
        self.zio_notification_alt = NotificationFactory(
            resource="zaakinformatieobject",
            actie="create",
            resource_url=self.zaak_informatie_object_alt["url"],
            hoofd_object=self.zaak_alt["url"],
        )
        self.zio_notification2_alt = NotificationFactory(
            resource="zaakinformatieobject",
            actie="create",
            resource_url=self.zaak_informatie_object2_alt["url"],
            hoofd_object=self.zaak2_alt["url"],
        )

    def install_mocks(self, m, *, res404: list[str] | None = None) -> "MockAPIData":
        if res404 is None:
            res404 = []
        for attr in res404:
            if not hasattr(self, attr):
                raise Exception("configuration error")

        if "case_roles" in res404:
            m.get(
                f"{ANOTHER_ZAKEN_ROOT}rollen?zaak={self.zaak_alt['url']}",
                status_code=404,
            )
        else:
            m.get(
                f"{ANOTHER_ZAKEN_ROOT}rollen?zaak={self.zaak_alt['url']}",
                json=paginated_response(self.case_roles_alt),
            )
            m.get(
                f"{ANOTHER_ZAKEN_ROOT}rollen?zaak={self.zaak2_alt['url']}",
                json=paginated_response(self.eherkenning_case_roles_alt),
            )

        if "status_history" in res404:
            m.get(
                f"{ANOTHER_ZAKEN_ROOT}statussen?zaak={self.zaak_alt['url']}",
                status_code=404,
            )
        else:
            m.get(
                f"{ANOTHER_ZAKEN_ROOT}statussen?zaak={self.zaak_alt['url']}",
                json=paginated_response(self.status_history_alt),
            )

        for resource_attr in [
            "zaak_alt",
            "zaak2_alt",
            "zaak_type_alt",
            "status_initial_alt",
            "status_final_alt",
            "status_type_initial_alt",
            "status_type_final_alt",
            "informatie_object_alt",
            "zaak_informatie_object_alt",
            "zaak_informatie_object2_alt",
            "informatie_object_extra_alt",
            "zaak_informatie_object_extra_alt",
        ]:
            resource = getattr(self, resource_attr)
            if resource_attr in res404:
                m.get(resource["url"], status_code=404)
            else:
                m.get(resource["url"], json=resource)

        return self

    @classmethod
    def setUpServices(cls):
        cls.api_group_alt = ZGWApiGroupConfigFactory(
            ztc_service__api_root=ANOTHER_CATALOGI_ROOT,
            zrc_service__api_root=ANOTHER_ZAKEN_ROOT,
            drc_service__api_root=ANOTHER_DOCUMENTEN_ROOT,
            form_service=None,
        )
