import json
import uuid

from django.db import connection
from django.test import tag

from zgw_consumers.constants import AuthTypes

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.openzaak.tests.factories import ServiceFactory
from open_inwoner.utils.tests.test_migrations import TestSuccessfulMigrations

_ESUITE_CONTACTMOMENT_UUID = "aaaaaaaa-aaaa-aaaa-aaaa-111111111111"


@tag("migrations")
class SeenAnswerMigrationTest(TestSuccessfulMigrations):
    """Migration 0040: the boolean 'KlantContactMomentAnswer.is_seen' flag is
    replaced with 'last_seen_answer_uuid'.

    eSuite holds one answer per contactmoment, so for its rows the flag translates
    exactly. A Klanten API row's url is the question's klantcontact rather than the
    answer's, so nothing there identifies the answer that was read.
    """

    app = "openklant"
    migrate_from = "0039_openklant2config_vragen_cache_timeout_and_more"
    migrate_to = "0040_klantcontactmomentanswer_last_seen_answer_uuid_and_more"

    def setUpBeforeMigration(self, apps):
        KlantContactMomentAnswer = apps.get_model(
            "openklant", "KlantContactMomentAnswer"
        )
        user = UserFactory()

        def _answer(url, is_seen):
            return KlantContactMomentAnswer.objects.create(
                user_id=user.id, contactmoment_url=url, is_seen=is_seen
            ).id

        self.seen_id = _answer(
            f"http://esuite.nl/contactmomenten/{_ESUITE_CONTACTMOMENT_UUID}",
            is_seen=True,
        )
        self.unseen_id = _answer(
            "http://esuite.nl/contactmomenten/aaaaaaaa-aaaa-aaaa-aaaa-222222222222",
            is_seen=False,
        )
        self.without_uuid_id = _answer(
            "http://esuite.nl/contactmomenten/legacy", is_seen=True
        )
        self.batch_ids = [
            _answer(f"http://esuite.nl/contactmomenten/{uuid.uuid4()}", is_seen=True)
            for _ in range(5)
        ]

    def _answers(self):
        return self.apps.get_model("openklant", "KlantContactMomentAnswer").objects

    def test_seen_esuite_answer_is_identified_by_its_contactmoment(self):
        self.assertEqual(
            self._answers().get(id=self.seen_id).last_seen_answer_uuid,
            uuid.UUID(_ESUITE_CONTACTMOMENT_UUID),
        )

    def test_unseen_answer_is_left_alone(self):
        self.assertIsNone(self._answers().get(id=self.unseen_id).last_seen_answer_uuid)

    def test_url_without_uuid_is_skipped_rather_than_failing(self):
        self.assertIsNone(
            self._answers().get(id=self.without_uuid_id).last_seen_answer_uuid
        )

    def test_every_seen_row_is_carried_over(self):
        carried_over = self._answers().filter(
            id__in=self.batch_ids, last_seen_answer_uuid__isnull=False
        )
        self.assertEqual(carried_over.count(), len(self.batch_ids))


def _make_openklant2_config(apps, service=None):
    OpenKlant2Config = apps.get_model("openklant", "OpenKlant2Config")
    return OpenKlant2Config.objects.create(service=service)


def _make_service(apps, **kwargs):
    Service = apps.get_model("zgw_consumers", "Service")
    service_obj = ServiceFactory(**kwargs)
    return Service.objects.get(id=service_obj.id)


@tag("migrations")
class MigrateLegacyServiceAuthTest(TestSuccessfulMigrations):
    """Migration 0041: a Service configured the old way (the actual token
    in `secret`, whatever `auth_type` happened to be set) is rewritten to
    the `auth_type=api_key` shape the fixed OpenKlant2Service client
    (commit 28c72c76) now reads its Authorization header from.
    """

    app = "openklant"
    migrate_from = "0040_klantcontactmomentanswer_last_seen_answer_uuid_and_more"
    migrate_to = "0041_migrate_openklant2_service_auth"

    def setUpBeforeMigration(self, apps):
        service = _make_service(
            apps,
            auth_type=AuthTypes.zgw,
            secret="abc123",
            header_key="",
            header_value="",
        )
        self.config_id = _make_openklant2_config(apps, service=service).id

    def _service(self):
        OpenKlant2Config = self.apps.get_model("openklant", "OpenKlant2Config")
        return OpenKlant2Config.objects.get(id=self.config_id).service

    def test_service_is_rewritten_to_api_key_auth(self):
        service = self._service()
        self.assertEqual(service.auth_type, AuthTypes.api_key)
        self.assertEqual(service.header_key, "Authorization")
        self.assertEqual(service.header_value, "Token abc123")


@tag("migrations")
class AlreadyMigratedServiceAuthTest(TestSuccessfulMigrations):
    """Migration 0041 is a no-op for a Service already in the expected
    `auth_type=api_key` shape, even if a leftover `secret` is still set."""

    app = "openklant"
    migrate_from = "0040_klantcontactmomentanswer_last_seen_answer_uuid_and_more"
    migrate_to = "0041_migrate_openklant2_service_auth"

    def setUpBeforeMigration(self, apps):
        service = _make_service(
            apps,
            auth_type=AuthTypes.api_key,
            secret="abc123",
            header_key="Authorization",
            header_value="Token untouched",
        )
        self.config_id = _make_openklant2_config(apps, service=service).id

    def test_service_is_left_untouched(self):
        OpenKlant2Config = self.apps.get_model("openklant", "OpenKlant2Config")
        service = OpenKlant2Config.objects.get(id=self.config_id).service
        self.assertEqual(service.header_value, "Token untouched")


@tag("migrations")
class ServiceWithoutSecretAuthTest(TestSuccessfulMigrations):
    """Migration 0041 leaves a Service alone if there is no `secret` to
    derive a token from, rather than writing an empty Authorization header."""

    app = "openklant"
    migrate_from = "0040_klantcontactmomentanswer_last_seen_answer_uuid_and_more"
    migrate_to = "0041_migrate_openklant2_service_auth"

    def setUpBeforeMigration(self, apps):
        service = _make_service(
            apps,
            auth_type=AuthTypes.zgw,
            secret="",
            header_key="",
            header_value="",
        )
        self.config_id = _make_openklant2_config(apps, service=service).id

    def test_service_is_left_untouched(self):
        OpenKlant2Config = self.apps.get_model("openklant", "OpenKlant2Config")
        service = OpenKlant2Config.objects.get(id=self.config_id).service
        self.assertEqual(service.auth_type, AuthTypes.zgw)
        self.assertEqual(service.header_key, "")


@tag("migrations")
class NoLinkedServiceAuthTest(TestSuccessfulMigrations):
    """Migration 0041 is a no-op when the openklant2 config has no linked
    Service at all (e.g. a fresh environment)."""

    app = "openklant"
    migrate_from = "0040_klantcontactmomentanswer_last_seen_answer_uuid_and_more"
    migrate_to = "0041_migrate_openklant2_service_auth"

    def setUpBeforeMigration(self, apps):
        self.config_id = _make_openklant2_config(apps, service=None).id

    def test_migration_does_not_raise(self):
        OpenKlant2Config = self.apps.get_model("openklant", "OpenKlant2Config")
        config = OpenKlant2Config.objects.get(id=self.config_id)
        self.assertIsNone(config.service_id)


def _text_with_link(text, href):
    return {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": text,
                        "marks": [{"type": "link", "attrs": {"href": href}}],
                    }
                ],
            }
        ],
    }


@tag("migrations")
class SanitizeProsemirrorLinkHrefsMigrationTest(TestSuccessfulMigrations):
    """
    Test migration 0042: strip unsafe hrefs from stored prosemirror link marks
    on ContactFormConfig.description_authenticated_user/description_anonymous_user.
    """

    migrate_from = "0041_migrate_openklant2_service_auth"
    migrate_to = "0042_sanitize_prosemirror_link_hrefs"
    app = "openklant"

    def setUpBeforeMigration(self, apps):
        Placeholder = apps.get_model("cms", "Placeholder")
        placeholder = Placeholder.objects.create(slot="content")

        # Use raw SQL to create the CMSPlugin row, avoiding treebeard fields
        # (depth, path, numchild) removed in CMS 4.
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO cms_cmsplugin
                    (placeholder_id, language, plugin_type, position, creation_date, changed_date)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                RETURNING id
                """,
                (placeholder.id, "nl", "ContactFormPlugin", 0),
            )
            self.plugin_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO openklant_contactformconfig
                    (cmsplugin_ptr_id, description_authenticated_user, description_anonymous_user)
                VALUES (%s, %s::jsonb, %s::jsonb)
                """,
                (
                    self.plugin_id,
                    json.dumps(_text_with_link("click", "javascript:alert(1)")),
                    json.dumps(_text_with_link("click", "https://example.com")),
                ),
            )

    def _get_field(self, field_name):
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {field_name}::text FROM openklant_contactformconfig "
                "WHERE cmsplugin_ptr_id = %s",
                (self.plugin_id,),
            )
            return json.loads(cursor.fetchone()[0])

    def test_unsafe_href_stripped_from_description_authenticated_user(self):
        doc = self._get_field("description_authenticated_user")
        text_node = doc["content"][0]["content"][0]
        self.assertEqual(text_node["marks"], [])

    def test_safe_href_preserved_on_description_anonymous_user(self):
        doc = self._get_field("description_anonymous_user")
        text_node = doc["content"][0]["content"][0]
        self.assertEqual(text_node["marks"][0]["attrs"]["href"], "https://example.com")
