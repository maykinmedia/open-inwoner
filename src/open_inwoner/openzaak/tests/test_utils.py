from django.test import TestCase

from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.constants import RolTypes, VertrouwelijkheidsAanduidingen
from zgw_consumers.api_models.zaken import Rol
from zgw_consumers.test import generate_oas_component

from open_inwoner.openzaak.api_models import InformatieObject
from open_inwoner.openzaak.utils import (
    get_role_identification_display,
    is_info_object_visible,
)


class TestUtils(TestCase):
    def test_filter_info_object_visibility(self):
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

    def test_get_role_identification_display(self):
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
            self.assertEqual(expected, get_role_identification_display(role))

        with self.subTest("natuurlijk_persoon > some fields"):
            role = get_role(
                RolTypes.natuurlijk_persoon,
                {
                    "geslachtsnaam": "Bazz",
                    "voorletters": "F.",
                },
            )
            expected = "F. Bazz"
            self.assertEqual(expected, get_role_identification_display(role))

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
            self.assertEqual(expected, get_role_identification_display(role))

        with self.subTest("niet_natuurlijk_persoon"):
            role = get_role(
                RolTypes.niet_natuurlijk_persoon,
                {
                    "statutaireNaam": "Foo Bar",
                },
            )
            expected = "Foo Bar"
            self.assertEqual(expected, get_role_identification_display(role))

        with self.subTest("vestiging"):
            role = get_role(
                RolTypes.vestiging,
                {
                    "handelsnaam": ["Foo Bar"],
                },
            )
            expected = "Foo Bar"
            self.assertEqual(expected, get_role_identification_display(role))

        with self.subTest("organisatorische_eenheid"):
            role = get_role(
                RolTypes.organisatorische_eenheid,
                {
                    "naam": "Foo Bar",
                },
            )
            expected = "Foo Bar"
            self.assertEqual(expected, get_role_identification_display(role))

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
            self.assertEqual(expected, get_role_identification_display(role))

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
            self.assertEqual(expected, get_role_identification_display(role))
