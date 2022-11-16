from django.test import TestCase

from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.constants import RolTypes
from zgw_consumers.api_models.zaken import Rol
from zgw_consumers.test import generate_oas_component

from open_inwoner.openzaak.utils import get_role_identification_display


class TestUtils(TestCase):
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
