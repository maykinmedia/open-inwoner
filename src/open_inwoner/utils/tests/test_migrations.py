import contextlib

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase


class TestMigrationsBase(TestCase):
    app = None
    migrate_from = None
    migrate_to = None
    extra_migrate_from: list[tuple[str, str]] = None
    """
    Test the effect of applying a migration
    Adapted from https://github.com/open-formulieren/open-forms/blob/e64c9368264d3f662542866e2d7d5ba15e0f265c/src/openforms/utils/tests/test_migrations.py
    """

    @contextlib.contextmanager
    def _immediate_constraints(self):
        try:
            # Force immediate constraint checks to stop error 'cannot ALTER TABLE "<..>"
            # because it has pending trigger events' in the tests
            with connection.cursor() as cursor:
                cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

            yield
        finally:
            with connection.cursor() as cursor:
                cursor.execute("SET CONSTRAINTS ALL DEFERRED")

    def _revert_to_migrate_from(self):
        assert self.migrate_from and self.migrate_to and self.app, (
            "TestCase '%s' must define migrate_from, migrate_to and app properties"
            % type(self).__name__
        )
        self.migrate_from = [(self.app, self.migrate_from)]

        # hack to fix issues where related models aren't in the correct state
        if self.extra_migrate_from:
            self.migrate_from += self.extra_migrate_from

        self.migrate_to = [(self.app, self.migrate_to)]
        executor = MigrationExecutor(connection)
        self.old_apps = executor.loader.project_state(self.migrate_from).apps

        with self._immediate_constraints():
            # Reverse to the original migration
            executor.migrate(self.migrate_from)

    def _apply_migration_to(self):
        # Run the migration to test
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()  # reload.
        with self._immediate_constraints():
            executor.migrate(self.migrate_to)
        self.apps = executor.loader.project_state(self.migrate_to).apps

    def setUpBeforeMigration(self, apps):
        pass


class TestSuccessfulMigrations(TestMigrationsBase):
    """Test a successful migration.

    Set the class attributes `app`, `migration_from`, and `migrate_to`. You
    can specify your pre-migration state in `setUpBeforeMigration()`, and
    consequently assert against the resulting state (in your test, do
    not import models directly but use:

    ```
    MyModel = self.apps.get_model(self.app, "MyModel")
    ```
    """

    def setUp(self):
        self._revert_to_migrate_from()
        self.setUpBeforeMigration(self.old_apps)
        self._apply_migration_to()


class TestFailingMigrations(TestMigrationsBase):
    """Test a migration which is expected to fail.

    Set the class attributes `app`, `migration_from`, and `migrate_to`. You
    can specify your pre-migration state in `setUpBeforeMigration()`, though
    you should not import models directly, but rather use:

    ```
    MyModel = self.apps.get_model(self.app, "MyModel")
    ```

    In your test, you can attempt to migration using `self.attempt_migration()`
    and assert against the expected exception:
    ```
    def test_migration_should_fail(self):
        # Setup failure conditions
        self.assertRaises(SomeError):
            self.attempt_migration()
    ```
    """

    def setUp(self):
        self._revert_to_migrate_from()
        self.setUpBeforeMigration(self.old_apps)

    def attempt_migration(self):
        self._apply_migration_to()
