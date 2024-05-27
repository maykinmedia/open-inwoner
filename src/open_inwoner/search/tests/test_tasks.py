from unittest.mock import Mock, patch

from django.test import TestCase

from ..tasks import rebuild_search_index


class SearchTaskTest(TestCase):
    @patch("open_inwoner.search.tasks.call_command")
    def test_task_calls_command(self, mock: Mock):
        rebuild_search_index()
        mock.assert_called_once_with("search_index", "--rebuild", "-f")
