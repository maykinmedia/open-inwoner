from unittest.mock import Mock, patch

from django.test import TestCase

from open_inwoner.celery import app as celery_app

from ..tasks import rebuild_search_index


class SearchTaskTest(TestCase):
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

    @patch("open_inwoner.search.tasks.call_command")
    def test_search_index_task_calls_command(
        self,
        mock: Mock,
    ):
        rebuild_search_index()

        mock.assert_called_once()
        self.assertEqual(mock.call_args.args, ("search_index", "--rebuild", "-f"))
