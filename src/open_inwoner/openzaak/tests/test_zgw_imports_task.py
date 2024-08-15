from unittest.mock import Mock, patch

from django.test import TestCase

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
    def test_zgw_import_task_calls_command(self, mock_call: Mock):
        import_zgw_data()

        mock_call.assert_called_once()
        self.assertEqual(mock_call.call_args.args, ("zgw_import_data",))
