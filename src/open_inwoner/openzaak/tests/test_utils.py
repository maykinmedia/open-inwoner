from django.test import TestCase

from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.constants import RolTypes, VertrouwelijkheidsAanduidingen
from zgw_consumers.test import generate_oas_component

from open_inwoner.openzaak.api_models import InformatieObject, Rol, Zaak, ZaakType
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.utils import (
    get_role_name_display,
    is_info_object_visible,
    is_zaak_visible,
)

ZAKEN_ROOT = "https://zaken.nl/api/v1/"
CATALOGI_ROOT = "https://catalogi.nl/api/v1/"
DOCUMENTEN_ROOT = "https://documenten.nl/api/v1/"


class TestUtils(TestCase):
    def test_is_info_object_visible(self):
        """
        openbaar
        beperkt_openbaar
        intern
        zaakvertrouwelijk
        vertrouwelijk
        confidentieel
        geheim
        zeer_geheim
        """
        max_level = VertrouwelijkheidsAanduidingen.vertrouwelijk

        cases = [
            # lowest below max_level
            (False, "in_bewerking", VertrouwelijkheidsAanduidingen.openbaar),
            (False, "ter_vaststelling", VertrouwelijkheidsAanduidingen.openbaar),
            (True, "definitief", VertrouwelijkheidsAanduidingen.openbaar),
            (False, "archief", VertrouwelijkheidsAanduidingen.openbaar),
            # just below max_level
            (False, "in_bewerking", VertrouwelijkheidsAanduidingen.zaakvertrouwelijk),
            (
                False,
                "ter_vaststelling",
                VertrouwelijkheidsAanduidingen.zaakvertrouwelijk,
            ),
            (True, "definitief", VertrouwelijkheidsAanduidingen.zaakvertrouwelijk),
            (False, "archief", VertrouwelijkheidsAanduidingen.zaakvertrouwelijk),
            # at max_level
            (False, "in_bewerking", VertrouwelijkheidsAanduidingen.vertrouwelijk),
            (False, "ter_vaststelling", VertrouwelijkheidsAanduidingen.vertrouwelijk),
            (True, "definitief", VertrouwelijkheidsAanduidingen.vertrouwelijk),
            (False, "archief", VertrouwelijkheidsAanduidingen.vertrouwelijk),
            # just above max_level
            (False, "in_bewerking", VertrouwelijkheidsAanduidingen.confidentieel),
            (False, "ter_vaststelling", VertrouwelijkheidsAanduidingen.confidentieel),
            (False, "definitief", VertrouwelijkheidsAanduidingen.confidentieel),
            (False, "archief", VertrouwelijkheidsAanduidingen.confidentieel),
            # highest above max_level
            (False, "in_bewerking", VertrouwelijkheidsAanduidingen.zeer_geheim),
            (False, "ter_vaststelling", VertrouwelijkheidsAanduidingen.zeer_geheim),
            (False, "definitief", VertrouwelijkheidsAanduidingen.zeer_geheim),
            (False, "archief", VertrouwelijkheidsAanduidingen.zeer_geheim),
        ]

        for expected, status, confidentiality in cases:
            with self.subTest(f"{status=} {confidentiality=} {expected}"):
                info_object = factory(
                    InformatieObject,
                    generate_oas_component(
                        "drc",
                        "schemas/EnkelvoudigInformatieObject",
                        status=status,
                        vertrouwelijkheidaanduiding=confidentiality,
                    ),
                )
                self.assertEqual(
                    expected, is_info_object_visible(info_object, max_level)
                )

        # test we don't leak on bad input
        with self.subTest(f"bad vertrouwelijkheidaanduiding in info object"):
            info_object = factory(
                InformatieObject,
                generate_oas_component(
                    "drc",
                    "schemas/EnkelvoudigInformatieObject",
                    status="definitief",
                    vertrouwelijkheidaanduiding="non_existent_key",
                ),
            )
            self.assertFalse(is_info_object_visible(info_object, max_level))

        with self.subTest(f"bad vertrouwelijkheidaanduiding as parameter"):
            info_object = factory(
                InformatieObject,
                generate_oas_component(
                    "drc",
                    "schemas/EnkelvoudigInformatieObject",
                    status="definitief",
                    vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.vertrouwelijk,
                ),
            )
            self.assertFalse(is_info_object_visible(info_object, "non_existent_key"))

    def test_is_zaak_visible(self):
        config = OpenZaakConfig.get_solo()
        self.assertEqual(
            config.zaak_max_confidentiality, VertrouwelijkheidsAanduidingen.openbaar
        )

        zaak = factory(
            Zaak,
            generate_oas_component(
                "zrc",
                "schemas/Zaak",
                uuid="d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
                url=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
                zaaktype=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f",
                identificatie="ZAAK-2022-0000000024",
                vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            ),
        )
        zaaktype = factory(
            ZaakType,
            generate_oas_component(
                "ztc",
                "schemas/ZaakType",
                url=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f",
                catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
                indicatieInternOfExtern="extern",
            ),
        )

        with self.subTest("raise when zaak.zaaktype not resolved"):
            with self.assertRaisesMessage(
                ValueError, "expected zaak.zaaktype to be resolved from url to model"
            ):
                is_zaak_visible(zaak)

        # resolve the zaaktype
        zaak.zaaktype = zaaktype

        with self.subTest("normal visible"):
            self.assertTrue(is_zaak_visible(zaak))

        with self.subTest("invisible when zaaktype intern"):
            zaaktype.indicatie_intern_of_extern = "intern"
            self.assertFalse(is_zaak_visible(zaak))

        with self.subTest("invisible when zaak vertrouwelijkheidaanduiding too high"):
            zaaktype.indicatie_intern_of_extern = "extern"
            zaak.vertrouwelijkheidaanduiding = VertrouwelijkheidsAanduidingen.geheim
            self.assertFalse(is_zaak_visible(zaak))

    def test_get_role_name_display(self):
        def get_role(type_: str, identification: dict) -> Rol:
            # helper for readability
            component = generate_oas_component(
                "zrc",
                "schemas/Rol",
                betrokkeneType=type_,
                betrokkeneIdentificatie=identification,
            )
            return factory(Rol, component)

        with self.subTest("natuurlijk_persoon > all fields"):
            role = get_role(
                RolTypes.natuurlijk_persoon,
                {
                    "geslachtsnaam": "Bazz",
                    "voorvoegselGeslachtsnaam": "van der",
                    "voorletters": "F.",
                    "voornamen": "Foo Bar",
                },
            )
            expected = "Foo Bar van der Bazz"
            self.assertEqual(expected, get_role_name_display(role))

        with self.subTest("natuurlijk_persoon > some fields"):
            role = get_role(
                RolTypes.natuurlijk_persoon,
                {
                    "geslachtsnaam": "Bazz",
                    "voorletters": "F.",
                },
            )
            expected = "F. Bazz"
            self.assertEqual(expected, get_role_name_display(role))

        with self.subTest("natuurlijk_persoon > bad data"):
            role = get_role(
                RolTypes.natuurlijk_persoon,
                {
                    "geslachtsnaam": "",
                    "voorvoegselGeslachtsnaam": "",
                    "voorletters": "",
                    "voornamen": "",
                },
            )
            expected = RolTypes.labels[RolTypes.natuurlijk_persoon]
            self.assertEqual(expected, get_role_name_display(role))

        with self.subTest("niet_natuurlijk_persoon"):
            role = get_role(
                RolTypes.niet_natuurlijk_persoon,
                {
                    "statutaireNaam": "Foo Bar",
                },
            )
            expected = "Foo Bar"
            self.assertEqual(expected, get_role_name_display(role))

        with self.subTest("vestiging"):
            role = get_role(
                RolTypes.vestiging,
                {
                    "handelsnaam": ["Foo Bar"],
                },
            )
            expected = "Foo Bar"
            self.assertEqual(expected, get_role_name_display(role))

        with self.subTest("organisatorische_eenheid"):
            role = get_role(
                RolTypes.organisatorische_eenheid,
                {
                    "naam": "Foo Bar",
                },
            )
            expected = "Foo Bar"
            self.assertEqual(expected, get_role_name_display(role))

        with self.subTest("medewerker > all fields"):
            role = get_role(
                RolTypes.medewerker,
                {
                    "achternaam": "Bazz",
                    "voorletters": "F. B.",
                    "voorvoegselAchternaam": "van der",
                },
            )
            expected = "F. B. van der Bazz"
            self.assertEqual(expected, get_role_name_display(role))

        with self.subTest("medewerker > some fields"):
            role = get_role(
                RolTypes.medewerker,
                {
                    "achternaam": "Bazz",
                    "voorletters": "",
                    "voorvoegselAchternaam": "",
                },
            )
            expected = "Bazz"
            self.assertEqual(expected, get_role_name_display(role))

        with self.subTest("medewerker > non-standard field name from Taiga #961"):
            role = get_role(
                RolTypes.medewerker,
                {
                    # this is not following spec
                    "volledigeNaam": "Bazz, Foo van der",
                },
            )
            expected = "Bazz, Foo van der"
            self.assertEqual(expected, get_role_name_display(role))
