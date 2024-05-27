import uuid
from unittest.mock import Mock, patch

from django.test import TestCase

from celery_once.tasks import AlreadyQueued

from open_inwoner.celery import app as celery_app
from open_inwoner.openzaak.tasks import import_zgw_data
from open_inwoner.utils.test import ClearCachesMixin


class ZGWImportTest(ClearCachesMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # manually patch the conf: it is a dynamic object that is hard to patch
        cls._old_eager = celery_app.conf.task_always_eager
        celery_app.conf.task_always_eager = False

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        celery_app.conf.task_always_eager = cls._old_eager

    @patch("open_inwoner.openzaak.tasks.call_command")
    def test_task_calls_command(self, mock_call: Mock):
        import_zgw_data()
        mock_call.assert_called_once_with("zgw_import_data")

    @patch("open_inwoner.celery.app.send_task")
    def test_task_runs_once(self, mock_send: Mock):
        # manually patch the task because it is not a normal class/method
        key = str(uuid.uuid4())

        def get_key(self, args=None, kwargs=None):
            return key

        import_zgw_data.get_key = get_key

        # add manual cleanup so we don't litter locks
        def cleanup():
            import_zgw_data.once_backend.clear_lock(key)

        self.addCleanup(cleanup)

        # actual test
        import_zgw_data.apply_async()
        with self.assertRaises(AlreadyQueued):
            import_zgw_data.apply_async()

        mock_send.assert_called_once()
