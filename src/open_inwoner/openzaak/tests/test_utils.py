from django.test import TestCase

from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.constants import RolTypes, VertrouwelijkheidsAanduidingen
from zgw_consumers.test import generate_oas_component

from open_inwoner.openzaak.api_models import InformatieObject, Zaak, ZaakType
from open_inwoner.openzaak.constants import InformatieObjectStatus
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.services import SkipReason, ZGWService
from open_inwoner.openzaak.tests.factories import generate_rol
from open_inwoner.openzaak.utils import get_role_name_display
from open_inwoner.utils.test import ClearCachesMixin

from .helpers import copy_with_new_uuid
from .shared import CATALOGI_ROOT, ZAKEN_ROOT


class TestUtils(ClearCachesMixin, TestCase):
    def _make_info_object(self, status, confidentiality):
        return factory(
            InformatieObject,
            generate_oas_component(
                "drc",
                "schemas/EnkelvoudigInformatieObject",
                status=status,
                vertrouwelijkheidaanduiding=confidentiality,
            ),
        )

    def test_is_info_object_visible(self):
        """
        Default visible statuses: definitief, gearchiveerd.

        Confidentiality levels (low to high):
        openbaar, beperkt_openbaar, intern, zaakvertrouwelijk, vertrouwelijk,
        confidentieel, geheim, zeer_geheim
        """
        max_level = VertrouwelijkheidsAanduidingen.vertrouwelijk
        visible_statuses = [
            InformatieObjectStatus.definitief,
            InformatieObjectStatus.gearchiveerd,
        ]

        cases = [
            # lowest below max_level
            (False, "in_bewerking", VertrouwelijkheidsAanduidingen.openbaar),
            (False, "ter_vaststelling", VertrouwelijkheidsAanduidingen.openbaar),
            (True, "definitief", VertrouwelijkheidsAanduidingen.openbaar),
            (True, "gearchiveerd", VertrouwelijkheidsAanduidingen.openbaar),
            (False, "archief", VertrouwelijkheidsAanduidingen.openbaar),
            # just below max_level
            (False, "in_bewerking", VertrouwelijkheidsAanduidingen.zaakvertrouwelijk),
            (
                False,
                "ter_vaststelling",
                VertrouwelijkheidsAanduidingen.zaakvertrouwelijk,
            ),
            (True, "definitief", VertrouwelijkheidsAanduidingen.zaakvertrouwelijk),
            (True, "gearchiveerd", VertrouwelijkheidsAanduidingen.zaakvertrouwelijk),
            (False, "archief", VertrouwelijkheidsAanduidingen.zaakvertrouwelijk),
            # at max_level
            (False, "in_bewerking", VertrouwelijkheidsAanduidingen.vertrouwelijk),
            (False, "ter_vaststelling", VertrouwelijkheidsAanduidingen.vertrouwelijk),
            (True, "definitief", VertrouwelijkheidsAanduidingen.vertrouwelijk),
            (True, "gearchiveerd", VertrouwelijkheidsAanduidingen.vertrouwelijk),
            (False, "archief", VertrouwelijkheidsAanduidingen.vertrouwelijk),
            # just above max_level
            (False, "in_bewerking", VertrouwelijkheidsAanduidingen.confidentieel),
            (False, "ter_vaststelling", VertrouwelijkheidsAanduidingen.confidentieel),
            (False, "definitief", VertrouwelijkheidsAanduidingen.confidentieel),
            (False, "gearchiveerd", VertrouwelijkheidsAanduidingen.confidentieel),
            (False, "archief", VertrouwelijkheidsAanduidingen.confidentieel),
            # highest above max_level
            (False, "in_bewerking", VertrouwelijkheidsAanduidingen.zeer_geheim),
            (False, "ter_vaststelling", VertrouwelijkheidsAanduidingen.zeer_geheim),
            (False, "definitief", VertrouwelijkheidsAanduidingen.zeer_geheim),
            (False, "gearchiveerd", VertrouwelijkheidsAanduidingen.zeer_geheim),
            (False, "archief", VertrouwelijkheidsAanduidingen.zeer_geheim),
        ]

        for expected, status, confidentiality in cases:
            with self.subTest(f"{status=} {confidentiality=} {expected}"):
                info_object = self._make_info_object(status, confidentiality)
                self.assertEqual(
                    expected,
                    ZGWService._is_info_object_visible(
                        info_object, max_level, visible_statuses
                    ),
                )

        # test we don't leak on bad input
        with self.subTest("bad vertrouwelijkheidaanduiding in info object"):
            info_object = self._make_info_object("definitief", "non_existent_key")
            self.assertFalse(
                ZGWService._is_info_object_visible(
                    info_object, max_level, visible_statuses
                )
            )

        with self.subTest("bad vertrouwelijkheidaanduiding as parameter"):
            info_object = self._make_info_object(
                "definitief", VertrouwelijkheidsAanduidingen.vertrouwelijk
            )
            self.assertFalse(
                ZGWService._is_info_object_visible(
                    info_object, "non_existent_key", visible_statuses
                )
            )

    def test_is_info_object_visible_custom_statuses(self):
        """document_visible_statuses controls which statuses are shown."""
        max_level = VertrouwelijkheidsAanduidingen.vertrouwelijk

        with self.subTest("only definitief visible"):
            visible_statuses = [InformatieObjectStatus.definitief]

            self.assertTrue(
                ZGWService._is_info_object_visible(
                    self._make_info_object(
                        "definitief", VertrouwelijkheidsAanduidingen.openbaar
                    ),
                    max_level,
                    visible_statuses,
                )
            )
            self.assertFalse(
                ZGWService._is_info_object_visible(
                    self._make_info_object(
                        "gearchiveerd", VertrouwelijkheidsAanduidingen.openbaar
                    ),
                    max_level,
                    visible_statuses,
                )
            )

        with self.subTest("in_bewerking added to visible statuses"):
            visible_statuses = [
                InformatieObjectStatus.definitief,
                InformatieObjectStatus.in_bewerking,
            ]

            self.assertTrue(
                ZGWService._is_info_object_visible(
                    self._make_info_object(
                        "in_bewerking", VertrouwelijkheidsAanduidingen.openbaar
                    ),
                    max_level,
                    visible_statuses,
                )
            )
            self.assertFalse(
                ZGWService._is_info_object_visible(
                    self._make_info_object(
                        "ter_vaststelling", VertrouwelijkheidsAanduidingen.openbaar
                    ),
                    max_level,
                    visible_statuses,
                )
            )

        with self.subTest("empty visible statuses disables status filtering"):
            for status in [
                "in_bewerking",
                "ter_vaststelling",
                "definitief",
                "gearchiveerd",
            ]:
                self.assertTrue(
                    ZGWService._is_info_object_visible(
                        self._make_info_object(
                            status, VertrouwelijkheidsAanduidingen.openbaar
                        ),
                        max_level,
                        [],
                    ),
                    msg=f"Expected {status} to be visible when document_visible_statuses is []",
                )

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
                ZGWService._is_zaak_visible(zaak)

        # resolve the zaaktype
        zaak.zaaktype = zaaktype

        with self.subTest("normal visible without status"):
            self.assertEqual(
                ZGWService._is_zaak_visible(zaak), (False, SkipReason.NO_STATUS)
            )

        config.show_cases_without_status = True
        config.save()

        with self.subTest("normal visible"):
            self.assertEqual(ZGWService._is_zaak_visible(zaak), (True, None))

        with self.subTest("invisible when zaaktype intern"):
            zaaktype.indicatie_intern_of_extern = "intern"
            self.assertEqual(
                ZGWService._is_zaak_visible(zaak), (False, SkipReason.INTERNAL_ZAAKTYPE)
            )

        with self.subTest("invisible when zaak vertrouwelijkheidaanduiding too high"):
            zaaktype.indicatie_intern_of_extern = "extern"
            zaak.vertrouwelijkheidaanduiding = VertrouwelijkheidsAanduidingen.geheim
            self.assertEqual(
                ZGWService._is_zaak_visible(zaak),
                (False, SkipReason.CONFIDENTIALITY_TOO_HIGH),
            )

        with self.subTest("invisible when zaaktype not properly resolved"):
            zaak.zaaktype = None
            self.assertEqual(
                ZGWService._is_zaak_visible(zaak), (False, SkipReason.NO_ZAAKTYPE)
            )

    def test_get_role_name_display(self):
        with self.subTest("natuurlijk_persoon > all fields"):
            role = generate_rol(
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
            role = generate_rol(
                RolTypes.natuurlijk_persoon,
                {
                    "geslachtsnaam": "Bazz",
                    "voorletters": "F.",
                },
            )
            expected = "F. Bazz"
            self.assertEqual(expected, get_role_name_display(role))

        with self.subTest("natuurlijk_persoon > bad data"):
            role = generate_rol(
                RolTypes.natuurlijk_persoon,
                {
                    "geslachtsnaam": "",
                    "voorvoegselGeslachtsnaam": "",
                    "voorletters": "",
                    "voornamen": "",
                },
            )
            expected = RolTypes.natuurlijk_persoon.label
            self.assertEqual(expected, get_role_name_display(role))

        with self.subTest("niet_natuurlijk_persoon"):
            role = generate_rol(
                RolTypes.niet_natuurlijk_persoon,
                {
                    "statutaireNaam": "Foo Bar",
                },
            )
            expected = "Foo Bar"
            self.assertEqual(expected, get_role_name_display(role))

        with self.subTest("vestiging"):
            role = generate_rol(
                RolTypes.vestiging,
                {
                    "handelsnaam": ["Foo Bar"],
                },
            )
            expected = "Foo Bar"
            self.assertEqual(expected, get_role_name_display(role))

        with self.subTest("organisatorische_eenheid"):
            role = generate_rol(
                RolTypes.organisatorische_eenheid,
                {
                    "naam": "Foo Bar",
                },
            )
            expected = "Foo Bar"
            self.assertEqual(expected, get_role_name_display(role))

        with self.subTest("medewerker > all fields"):
            role = generate_rol(
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
            role = generate_rol(
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
            role = generate_rol(
                RolTypes.medewerker,
                {
                    # this is not following spec
                    "volledigeNaam": "Bazz, Foo van der",
                },
            )
            expected = "Bazz, Foo van der"
            self.assertEqual(expected, get_role_name_display(role))


class TestHelpers(TestCase):
    def test_copy_with_new_uuid(self):
        data = {
            "url": "http://api/zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "data": [1, 2, 3],
        }
        res = copy_with_new_uuid(data)
        # its a deepcopy
        self.assertIsNot(data, res)
        self.assertIsNot(data["data"], res["data"])
        self.assertEqual(data["data"], res["data"])

        # uuid in url updated
        self.assertNotEqual(data["url"], res["url"])

        data = {
            "uuid": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "url": "http://api/zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        }
        res = copy_with_new_uuid(data)
        self.assertIsNot(data, res)
        # uuid AND url updated
        self.assertNotEqual(data["uuid"], res["uuid"])
        self.assertIn(data["uuid"], data["url"])
