import io
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import resolve_url
from django.urls import reverse
from django.utils.encoding import force_str

from django_otp import DEVICE_ID_SESSION_KEY
from furl import furl
from PIL import Image
from timeline_logger.models import TimelineLog
from two_factor.utils import default_device


class Lookups:
    """
    lookups for the message of a JSONField
    """

    exact = "exact"
    icontains = "icontains"

    startswith = "startswith"
    istartswith = "istartswith"
    endswith = "endswith"
    iendswith = "iendswith"
    iexact = "iexact"
    regex = "regex"
    iregex = "iregex"


class AssertTimelineLogMixin:
    def assertTimelineLog(
        self, message, *, level=None, lookup=Lookups.exact
    ) -> TimelineLog:
        kwargs = {
            f"extra_data__message__{lookup}": force_str(message),
        }
        if level is not None:
            kwargs["extra_data__log_level"] = level

        logs = list(TimelineLog.objects.filter(**kwargs))
        count = len(logs)
        if count == 0:
            self.fail(
                f"cannot find TimelineLog with {kwargs}, got:\n{self.getTimelineLogDump()}"
            )
        elif count > 1:
            self.fail(
                f"found {count} TimelineLogs with {kwargs}, got:\n{self.getTimelineLogDump()}"
            )

        return logs[0]

    def getTimelineLogDump(self) -> str:
        ret = []
        qs = TimelineLog.objects.all()
        c = qs.count()
        if c:
            ret.append(f"total {c} timelinelogs:")
        else:
            ret.append(f"total {c} timelinelogs")

        for log in qs:
            message = log.extra_data.get("message")
            log_level = log.extra_data.get("log_level")
            if log_level:
                log_level = logging.getLevelName(log_level)
            else:
                log_level = "NO_LEVEL"
            msg = f"  {log_level}: {message}"
            ret.append(msg)
        return "\n".join(ret)

    def dumpTimelineLog(self):
        print(self.getTimelineLogDump())


class AssertFormMixin:
    def assertFormExactFields(
        self, form, field_names, *, with_csrf=True, drop_no_name=True
    ):
        """
        check if a form has expected fields, usually from WebTest

        - with_csrf: auto-adds adds the csrfmiddlewaretoken
        - drop_no_name: ignore the empty field created by the submit button
        """
        expect_names = set(field_names)
        if with_csrf:
            expect_names.add("csrfmiddlewaretoken")

        have_names = set(form.fields.keys())
        if drop_no_name:
            have_names.discard("")

        self.assertEqual(
            have_names,
            expect_names,
            "-> first set is actual in form, second set is expected",
        )


class AssertRedirectsMixin:
    def assertRedirectsLogin(
        self, response, *, next: str = None, with_host: bool = False
    ):
        url = reverse("login")
        if next is not None:
            url = furl(url).set(args={"next": str(next)}).url
        if with_host:
            url = furl(url).set(scheme="http", host="testserver").url
        self.assertRedirects(response, url)

    def assertRedirectsLogout(
        self, response, *, next: str = None, with_host: bool = False
    ):
        url = reverse("logout")
        if next is not None:
            url = furl(url).set(args={"next": str(next)}).url
        if with_host:
            url = furl(url).set(scheme="http", host="testserver").url
        self.assertRedirects(response, url)


class TwoFactorUserTestMixin:
    """
    mixin to setup two-factor verified users

    copied from: https://github.com/jazzband/django-two-factor-auth/blob/21962acf9717985a1b2bb019de4c6f2f982767a1/tests/utils.py#LL12C17-L12C17

    usage examples: https://github.com/jazzband/django-two-factor-auth/blob/21962acf9717985a1b2bb019de4c6f2f982767a1/tests/test_views_mixins.py#L12

    verified user:
        self.create_user()
        self.enable_otp()  # create OTP before login, so verified
        self.login_user()
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.login_url = resolve_url(settings.LOGIN_URL)
        cls.User = get_user_model()

    def setUp(self):
        super().setUp()
        self._passwords = {}

    def create_user(self, email="bouke@example.com", password="secret", **kwargs):
        user = self.User.objects.create_user(email=email, password=password, **kwargs)
        self._passwords[user] = password
        return user

    def login_user(self):
        user = list(self._passwords.keys())[0]
        username = user.get_username()
        assert self.client.login(username=username, password=self._passwords[user])
        if default_device(user):
            session = self.client.session
            session[DEVICE_ID_SESSION_KEY] = default_device(user).persistent_id
            session.save()

    def enable_otp(self, user=None):
        if user is None:
            user = list(self._passwords.keys())[0]
        return user.totpdevice_set.create(name="default")


def create_image_bytes(img_file=None):
    if img_file:
        img = Image.open(img_file)
    else:
        img = Image.new("RGB", (10, 10))
    image_io = io.BytesIO()
    img.save(image_io, format="JPEG")
    img_bytes = image_io.getvalue()

    return img_bytes
