# from django.test import RequestFactory
# from django.test import TestCase

# import requests_mock
# from zgw_consumers.constants import APITypes

# from open_inwoner.accounts.tests.factories import (
#     DigidUserFactory,
#     eHerkenningUserFactory,
# )
# from open_inwoner.openzaak.tests.factories import ServiceFactory
# from open_inwoner.utils.tests.helpers import AssertTimelineLogMixin

# from .. clients import build_client
# from .. models import OpenKlantConfig
# from .. services import update_user_from_klant

# KLANTEN_ROOT = "https://klanten.nl/api/v1/"


# @requests_mock.Mocker()
# class KlantenClientTest(AssertTimelineLogMixin, TestCase):
#     @classmethod
#     def setUpTestData(cls):
#         config = OpenKlantConfig.get_solo()
#         config.klanten_service = ServiceFactory(
#             api_root=KLANTEN_ROOT, api_type=APITypes.kc,
#         )
#         config.save()

#         cls.klant = {
#             "bronorganisatie": "123456789",
#             "klantnummer": "87654321",
#             "subjectIdentificatie": {
#                 "inpBsn": "123456789",
#             },
#             "subjectType": "natuurlijk_persoon",
#             "url": f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
#         }

#     def test_create_klant_for_bsn(self, m):
#         digid_user = DigidUserFactory(
#             bsn="123456789",
#             email="digid@example.com",
#             phonenumber="123456789",
#         )
#         eherkenning_user = eHerkenningUserFactory(
#             kvk="12345678",
#             email="company@example.com",
#         )

#         m.get(
#             f"{KLANTEN_ROOT}klanten?subjectNatuurlijkPersoon__inpBsn=123456789", json={"count": 0, "results": []}
#         )
#         m.post(
#             f"{KLANTEN_ROOT}klanten", json=self.klant
#         )

#         # client = build_client("klanten")
#         # # klant = client.create_klant(digid_user.bsn)
#         # klant = client.create_klant(eherkenning_user.kvk)
#         # import pdbr;pdbr.set_trace()

#         request = RequestFactory().get("/dummy")
#         request.user = digid_user

#         user, klant = update_user_from_klant(request)

#         self.assertTimelineLog("created klant for user")
#         import pdbr;pdbr.set_trace()
