from django.test import tag
from django.urls import reverse
from django.utils.translation import gettext as _

from django_webtest import WebTest
from freezegun import freeze_time
from timeline_logger.models import TimelineLog

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.utils.logentry import LOG_ACTIONS

from .utils import ESMixin


@tag("no-parallel")
@freeze_time("2021-10-18 13:00:00")
class TestLogging(ESMixin, WebTest):
    def test_search_query_of_logged_in_user_is_logged(self):
        user = UserFactory()
        form = self.app.get(reverse("search:search"), user=user).forms["search-form"]
        form["query"] = "search for something"
        form.submit()

        log_entry = TimelineLog.objects.all()[1]

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, user.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": (_("search query: {query}")).format(
                    query="search for something"
                ),
                "action_flag": list(LOG_ACTIONS[4]),
                "content_object_repr": str(user),
            },
        )

    def test_search_query_of_anonymous_user_is_not_logged(self):
        form = self.app.get(reverse("search:search")).forms["search-form"]
        form["query"] = "search for something"
        form.submit()

        log_entries = TimelineLog.objects.count()

        self.assertEqual(log_entries, 0)
