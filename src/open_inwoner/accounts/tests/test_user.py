from datetime import date

from django.test import TestCase

from freezegun import freeze_time

from ..models import User


class UserTests(TestCase):
    @freeze_time("2021-07-07 12:00:00")
    def test_get_age_same_day(self):
        with freeze_time("1990-07-07"):
            user = User(birthday=date.today())
        self.assertEqual(user.get_age(), 31)

    @freeze_time("2021-07-07 12:00:00")
    def test_get_age_day_before(self):
        with freeze_time("1990-07-08"):
            user = User(birthday=date.today())
        self.assertEqual(user.get_age(), 30)

    @freeze_time("2021-07-07 12:00:00")
    def test_get_age_day_after(self):
        with freeze_time("1990-07-06"):
            user = User(birthday=date.today())
        self.assertEqual(user.get_age(), 31)

    @freeze_time("2021-07-07 12:00:00")
    def test_get_age_young(self):
        with freeze_time("2014-01-07"):
            user = User(birthday=date.today())
        self.assertEqual(user.get_age(), 7)
