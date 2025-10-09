from django.test import TestCase

from open_inwoner.kvk.views import CompanyBranchChoiceView


class KvkBranchesComboBoxDataTestCase(TestCase):
    def setUp(self):
        self.view = CompanyBranchChoiceView()

    def test_vestigingen_combobox_data_with_branches(self):
        """Test JSON structure with rechtspersoon, hoofdvestiging, and nevenvestiging"""
        branches = [
            {"kvkNummer": "12345678", "naam": "Test Company", "type": "rechtspersoon"},
            {
                "kvkNummer": "12345678",
                "vestigingsnummer": "1234",
                "naam": "Test Company",
                "type": "hoofdvestiging",
                "adres": {
                    "binnenlandsAdres": {
                        "straatnaam": "Teststraat",
                        "huisnummer": 42,
                        "huisnummerToevoeging": "A",
                        "plaats": "Amsterdam",
                    }
                },
            },
            {
                "kvkNummer": "12345678",
                "vestigingsnummer": "9876",
                "naam": "Test Company Branch",
                "type": "nevenvestiging",  # Non-main branch
                "adres": {
                    "binnenlandsAdres": {
                        "straatnaam": "Branchstraat",
                        "huisnummer": 10,
                        "plaats": "Rotterdam",
                    }
                },
            },
        ]
        data = self.view.get_vestigingen_combobox_data(branches, selected_id="1234")

        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 3)
        self.assertEqual(data["selected_id"], "1234")

        with self.subTest("rechtspersoon item"):
            self.assertEqual(data["items"][0]["id"], "rechtspersoon")
            self.assertEqual(
                data["items"][0]["rechtspersoonInfo"],
                "Selecteer de rechtspersoon (geen vestiging)",
            )

        with self.subTest("hoofdvestiging item"):
            self.assertEqual(data["items"][1]["id"], "1234")
            self.assertIn("Hoofdvestiging", data["items"][1]["vestigingInfo"])
            # Updated assert to include huisnummerToevoeging
            self.assertEqual(data["items"][1]["addressInfo"], "Teststraat 42 A")
            self.assertEqual(data["items"][1]["cityInfo"], "Amsterdam")

        with self.subTest("nevenvestiging item"):
            self.assertEqual(data["items"][2]["id"], "9876")
            # Should NOT contain "Hoofdvestiging" text
            self.assertNotIn("Hoofdvestiging", data["items"][2]["vestigingInfo"])
            self.assertEqual(data["items"][2]["vestigingInfo"], "Vestiging: 9876")
            self.assertEqual(data["items"][2]["addressInfo"], "Branchstraat 10")
            self.assertEqual(data["items"][2]["cityInfo"], "Rotterdam")

    def test_vestigingen_combobox_data_handles_combined_address_field(self):
        """Test straatHuisnummer combined field takes precedence"""
        branches = [
            {
                "naam": "Test Company",
                "vestigingsnummer": "5678",
                "type": "hoofdvestiging",
                "adres": {
                    "binnenlandsAdres": {
                        "straatHuisnummer": "Kalverstraat 123",
                        "plaats": "Amsterdam",
                    }
                },
            }
        ]

        data = self.view.get_vestigingen_combobox_data(branches)

        self.assertEqual(data["items"][0]["addressInfo"], "Kalverstraat 123")

    def test_vestigingen_combobox_data_with_empty_branches(self):
        """Test empty branches list returns valid empty structure"""
        data = self.view.get_vestigingen_combobox_data([])

        self.assertEqual(data["items"], [])
        self.assertIn("selected_id", data)
