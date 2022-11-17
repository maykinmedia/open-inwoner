from django.test import TestCase

from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen
from zgw_consumers.test import generate_oas_component

from open_inwoner.openzaak.info_objects import InformatieObject
from open_inwoner.openzaak.utils import filter_info_object_visibility


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
                    expected, filter_info_object_visibility(info_object, max_level)
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
            self.assertFalse(filter_info_object_visibility(info_object, max_level))

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
            self.assertFalse(
                filter_info_object_visibility(info_object, "non_existent_key")
            )
