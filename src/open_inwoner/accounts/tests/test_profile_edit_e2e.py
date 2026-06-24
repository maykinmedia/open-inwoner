from django.test import override_settings, tag

from playwright.sync_api import expect

from open_inwoner.accounts.choices import DigitalAddressType, LoginTypeChoices
from open_inwoner.accounts.models import DigitalAddress
from open_inwoner.cms.tests import cms_tools
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.utils.tests.playwright import PlaywrightSyncLiveServerTestCase

from .factories import DigidUserFactory, DigitalAddressFactory


@tag("e2e")
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class ProfileEditE2ETest(PlaywrightSyncLiveServerTestCase):
    def setUp(self):
        super().setUp()

        config = SiteConfiguration.get_solo()
        cms_tools.create_homepage()
        config.cookie_info_text = ""
        config.save()

        self.user = DigidUserFactory.create(
            email="user@example.com",
            phonenumber="0612345678",
        )
        DigitalAddressFactory.create(
            user=self.user,
            type=DigitalAddressType.email,
            value="user@example.com",
            login_type=LoginTypeChoices.digid,
            is_standard_for_type=True,
        )
        DigitalAddressFactory.create(
            user=self.user,
            type=DigitalAddressType.phone,
            value="0612345678",
            login_type=LoginTypeChoices.digid,
            is_standard_for_type=True,
        )
        self.user_login_state = self.get_user_bsn_login_state(self.user)

    def _open_edit_page(self, context):
        page = context.new_page()
        page.goto(self.live_reverse("profile:edit"))
        return page

    def test_add_second_email_address(self):
        """A second email can be added via the + button and is persisted on save."""
        context = self.get_context(storage_state=self.user_login_state)
        page = self._open_edit_page(context)

        email_section = page.locator(
            '[data-addition-input][data-prefix="email_addresses"]'
        )
        add_button = page.locator("#email_addresses-add-btn")

        expect(email_section.locator("[data-addition-input-row]")).to_have_count(1)

        add_button.click()

        expect(email_section.locator("[data-addition-input-row]")).to_have_count(2)

        email_section.locator("[data-addition-input-row]").nth(1).locator(
            '[name$="-value"]'
        ).fill("second@example.com")

        page.get_by_role("button", name="Sla wijzigingen op").click()
        page.wait_for_url(self.live_reverse("profile:detail", star=True))

        self.assertEqual(
            DigitalAddress.objects.filter(
                user=self.user, type=DigitalAddressType.email
            ).count(),
            2,
        )
        self.assertTrue(
            DigitalAddress.objects.filter(
                user=self.user,
                type=DigitalAddressType.email,
                value="second@example.com",
            ).exists()
        )

    def test_update_existing_email_address(self):
        """The value of an existing email address can be changed and is persisted."""
        context = self.get_context(storage_state=self.user_login_state)
        page = self._open_edit_page(context)

        email_section = page.locator(
            '[data-addition-input][data-prefix="email_addresses"]'
        )
        value_input = email_section.locator("[data-addition-input-row]").first.locator(
            '[name$="-value"]'
        )

        expect(value_input).to_have_value("user@example.com")

        value_input.fill("updated@example.com")
        page.get_by_role("button", name="Sla wijzigingen op").click()
        page.wait_for_url(self.live_reverse("profile:detail", star=True))

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "updated@example.com")
        self.assertTrue(
            DigitalAddress.objects.filter(
                user=self.user,
                type=DigitalAddressType.email,
                value="updated@example.com",
                is_standard_for_type=True,
            ).exists()
        )

    def test_add_duplicate_email_address_is_rejected(self):
        """Submitting a duplicate email value shows a formset error and leaves DB unchanged."""
        context = self.get_context(storage_state=self.user_login_state)
        page = self._open_edit_page(context)

        email_section = page.locator(
            '[data-addition-input][data-prefix="email_addresses"]'
        )
        page.locator("#email_addresses-add-btn").click()
        email_section.locator("[data-addition-input-row]").nth(1).locator(
            '[name$="-value"]'
        ).fill("user@example.com")

        page.get_by_role("button", name="Sla wijzigingen op").click()
        page.wait_for_load_state("networkidle")

        expect(page).to_have_url(self.live_reverse("profile:edit"))
        expect(email_section.get_by_role("alert")).to_be_visible()
        self.assertEqual(
            DigitalAddress.objects.filter(
                user=self.user, type=DigitalAddressType.email
            ).count(),
            1,
        )

    def test_add_malformed_email_shows_validation_error(self):
        """Submitting a malformed email value shows a field error and leaves DB unchanged."""
        context = self.get_context(storage_state=self.user_login_state)
        page = self._open_edit_page(context)

        email_section = page.locator(
            '[data-addition-input][data-prefix="email_addresses"]'
        )
        page.locator("#email_addresses-add-btn").click()
        email_section.locator("[data-addition-input-row]").nth(1).locator(
            '[name$="-value"]'
        ).fill("not-an-email")

        page.get_by_role("button", name="Sla wijzigingen op").click()
        page.wait_for_load_state("networkidle")

        expect(page).to_have_url(self.live_reverse("profile:edit"))
        expect(
            email_section.locator("[data-addition-input-row]")
            .nth(1)
            .get_by_role("alert")
        ).to_be_visible()
        self.assertEqual(
            DigitalAddress.objects.filter(
                user=self.user, type=DigitalAddressType.email
            ).count(),
            1,
        )

    def test_add_malformed_phone_shows_validation_error(self):
        """Submitting a malformed phone number shows a field error and leaves DB unchanged."""
        context = self.get_context(storage_state=self.user_login_state)
        page = self._open_edit_page(context)

        phone_section = page.locator(
            '[data-addition-input][data-prefix="phone_addresses"]'
        )
        page.locator("#phone_addresses-add-btn").click()
        phone_section.locator("[data-addition-input-row]").nth(1).locator(
            '[name$="-value"]'
        ).fill("not-a-phone")

        page.get_by_role("button", name="Sla wijzigingen op").click()
        page.wait_for_load_state("networkidle")

        expect(page).to_have_url(self.live_reverse("profile:edit"))
        expect(
            phone_section.locator("[data-addition-input-row]")
            .nth(1)
            .get_by_role("alert")
        ).to_be_visible()
        self.assertEqual(
            DigitalAddress.objects.filter(
                user=self.user, type=DigitalAddressType.phone
            ).count(),
            1,
        )

    def test_change_primary_email_address(self):
        """Switching the primary checkbox to a different email persists and updates user.email."""
        DigitalAddressFactory.create(
            user=self.user,
            type=DigitalAddressType.email,
            value="second@example.com",
            login_type=LoginTypeChoices.digid,
            is_standard_for_type=False,
        )

        context = self.get_context(storage_state=self.user_login_state)
        page = self._open_edit_page(context)

        email_section = page.locator(
            '[data-addition-input][data-prefix="email_addresses"]'
        )
        first_row = email_section.locator("[data-addition-input-row]").nth(0)
        second_row = email_section.locator("[data-addition-input-row]").nth(1)

        first_primary = first_row.locator('[name$="-is_standard_for_type"]')
        second_primary = second_row.locator('[name$="-is_standard_for_type"]')

        expect(first_primary).to_be_checked()
        expect(second_primary).not_to_be_checked()

        first_row.locator("label.radio__label").click()
        second_row.locator("label.radio__label").click()

        page.get_by_role("button", name="Sla wijzigingen op").click()
        page.wait_for_url(self.live_reverse("profile:detail", star=True))

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "second@example.com")
        self.assertTrue(
            DigitalAddress.objects.filter(
                user=self.user,
                type=DigitalAddressType.email,
                value="second@example.com",
                is_standard_for_type=True,
            ).exists()
        )
        self.assertFalse(
            DigitalAddress.objects.filter(
                user=self.user,
                type=DigitalAddressType.email,
                value="user@example.com",
                is_standard_for_type=True,
            ).exists()
        )

    def test_delete_non_primary_phone_number(self):
        """A non-primary phone number can be removed; the primary phone stays."""
        DigitalAddressFactory.create(
            user=self.user,
            type=DigitalAddressType.phone,
            value="0687654321",
            login_type=LoginTypeChoices.digid,
            is_standard_for_type=False,
        )

        context = self.get_context(storage_state=self.user_login_state)
        page = self._open_edit_page(context)

        phone_section = page.locator(
            '[data-addition-input][data-prefix="phone_addresses"]'
        )
        expect(phone_section.locator("[data-addition-input-row]")).to_have_count(2)

        # The second row is the non-primary one; click its delete button.
        second_row = phone_section.locator("[data-addition-input-row]").nth(1)
        second_row.locator("[data-delete-row]").click()

        # Row is hidden but still in DOM (pending server-side delete).
        expect(second_row).to_be_hidden()

        page.get_by_role("button", name="Sla wijzigingen op").click()
        page.wait_for_url(self.live_reverse("profile:detail", star=True))

        self.assertEqual(
            DigitalAddress.objects.filter(
                user=self.user,
                type=DigitalAddressType.phone,
            ).count(),
            1,
        )
        self.assertTrue(
            DigitalAddress.objects.filter(
                user=self.user,
                type=DigitalAddressType.phone,
                is_standard_for_type=True,
            ).exists()
        )
