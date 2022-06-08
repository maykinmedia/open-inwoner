from django.contrib.admin.models import ADDITION, CHANGE
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest
from freezegun import freeze_time
from privates.test import temp_private_root
from timeline_logger.models import TimelineLog
from webtest import Upload

from open_inwoner.accounts.models import Action
from open_inwoner.accounts.tests.factories import ActionFactory, UserFactory
from open_inwoner.utils.logentry import LOG_ACTIONS

from ..models import Plan
from .factories import PlanFactory


@freeze_time("2021-10-18 13:00:00")
class TestPlans(WebTest):
    def setUp(self):
        self.user = UserFactory()
        self.plan = PlanFactory(created_by=self.user)

    def test_created_plan_is_logged(self):
        plan = PlanFactory.build(created_by=self.user)
        form = self.app.get(reverse("plans:plan_create"), user=self.user).forms[
            "plan-form"
        ]
        form["title"] = plan.title
        form["end_date"] = plan.end_date
        form.submit()

        log_entry = TimelineLog.objects.last()

        self.assertEquals(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEquals(
            log_entry.content_object.id, Plan.objects.get(title=plan.title).id
        )
        self.assertEquals(
            log_entry.extra_data,
            {
                "message": _("plan was created"),
                "action_flag": list(LOG_ACTIONS[ADDITION]),
                "content_object_repr": plan.title,
            },
        )

    def test_modified_plan_is_logged(self):
        form = self.app.get(
            reverse("plans:plan_edit", kwargs={"uuid": self.plan.uuid}), user=self.user
        ).forms["plan-form"]
        form["title"] = "Updated title"
        form.submit()
        log_entry = TimelineLog.objects.last()

        self.assertEquals(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEquals(log_entry.content_object.id, self.plan.id)
        self.assertEquals(
            log_entry.extra_data,
            {
                "message": _("plan was modified"),
                "action_flag": list(LOG_ACTIONS[CHANGE]),
                "content_object_repr": "Updated title",
            },
        )

    def test_plan_goal_modified_is_logged(self):
        form = self.app.get(
            reverse("plans:plan_edit_goal", kwargs={"uuid": self.plan.uuid}),
            user=self.user,
        ).forms["goal-edit"]

        form["goal"] = "Some text"
        form.submit()
        log_entry = TimelineLog.objects.last()

        self.assertEquals(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEquals(log_entry.content_object.id, self.plan.id)
        self.assertEquals(
            log_entry.extra_data,
            {
                "message": _("plan goal was modified"),
                "action_flag": list(LOG_ACTIONS[CHANGE]),
                "content_object_repr": self.plan.title,
            },
        )

    @temp_private_root()
    def test_plan_file_upload_is_logged(self):
        form = self.app.get(
            reverse("plans:plan_add_file", kwargs={"uuid": self.plan.uuid}),
            user=self.user,
        ).forms["document-create"]

        form["file"] = Upload("readme.xlsx", b"data", "application/vnd.ms-excel")
        form["name"] = "readme"
        form.submit()
        log_entry = TimelineLog.objects.last()

        self.assertEquals(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEquals(log_entry.content_object.id, self.plan.id)
        self.assertEquals(
            log_entry.extra_data,
            {
                "message": _("file was uploaded"),
                "action_flag": list(LOG_ACTIONS[4]),
                "content_object_repr": self.plan.title,
            },
        )

    def test_plan_action_created_is_logged(self):
        action = ActionFactory.build(created_by=self.user)
        form = self.app.get(
            reverse("plans:plan_action_create", kwargs={"uuid": self.plan.uuid}),
            user=self.user,
        ).forms["action-create"]
        form["name"] = action.name
        form.submit()
        log_entry = TimelineLog.objects.last()

        self.assertEquals(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEquals(log_entry.content_object.id, Action.objects.first().id)
        self.assertEquals(
            log_entry.extra_data,
            {
                "message": _("action was created via plan"),
                "action_flag": list(LOG_ACTIONS[ADDITION]),
                "content_object_repr": action.name,
            },
        )

    def test_plan_action_modified_is_logged(self):
        action = ActionFactory(created_by=self.user)
        form = self.app.get(
            reverse(
                "plans:plan_action_edit",
                kwargs={"plan_uuid": self.plan.uuid, "uuid": action.uuid},
            ),
            user=self.user,
        ).forms["action-create"]
        form["name"] = "Updated name"
        form.submit()
        log_entry = TimelineLog.objects.last()

        self.assertEquals(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEquals(log_entry.content_object.id, Action.objects.first().id)
        self.assertEquals(
            log_entry.extra_data,
            {
                "message": _("Changed: Naam."),
                "action_flag": list(LOG_ACTIONS[CHANGE]),
                "content_object_repr": "Updated name",
            },
        )

    def test_plan_export_is_logged(self):
        self.app.get(
            reverse("plans:plan_export", kwargs={"uuid": self.plan.uuid}),
            user=self.user,
        )
        log_entry = TimelineLog.objects.last()

        self.assertEquals(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEquals(log_entry.content_object.id, self.user.id)
        self.assertEquals(
            log_entry.extra_data,
            {
                "message": _("file plan_{plan_uuid}.pdf was exported").format(
                    plan_uuid=self.plan.uuid
                ),
                "action_flag": list(LOG_ACTIONS[4]),
                "content_object_repr": self.user.email,
            },
        )
