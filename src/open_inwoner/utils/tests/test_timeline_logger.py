from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest
from freezegun import freeze_time
from timeline_logger.models import TimelineLog

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.plans.models import Plan
from open_inwoner.plans.tests.factories import PlanFactory

from ..admin import CustomTimelineLogAdmin
from ..logentry import LOG_ACTIONS


class TestAdminTimelineLogging(WebTest):
    csrf_checks = False

    def setUp(self):
        self.user = UserFactory(is_superuser=True, is_staff=True)
        self.plan = PlanFactory.build()

    def add_instance(self):
        url = reverse("admin:plans_plan_add")
        form = self.app.get(url, user=self.user).forms.get("plan_form")
        form["title"] = self.plan.title
        form["goal"] = self.plan.goal
        form["description"] = self.plan.description
        form["end_date"] = self.plan.end_date
        form["created_by"] = self.user.id
        form.submit()

    @freeze_time("2021-10-18 13:00:00")
    def test_added_object_is_logged(self):
        self.add_instance()

        log_entry = TimelineLog.objects.last()
        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, Plan.objects.first().id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("Toegevoegd."),
                "action_flag": list(LOG_ACTIONS[ADDITION]),
                "content_object_repr": str(self.plan),
            },
        )

    @freeze_time("2021-10-18 13:00:00")
    def test_changed_object_is_logged(self):
        plan = PlanFactory(created_by=self.user)
        url = reverse("admin:plans_plan_change", kwargs={"object_id": plan.id})
        form = self.app.get(url, user=self.user).forms.get("plan_form")
        form["title"] = "Updated"
        form["goal"] = "Foo"
        form["end_date"] = self.plan.end_date
        form["created_by"] = self.user.id
        form.submit()

        log_entry = TimelineLog.objects.last()
        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, Plan.objects.first().id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": "Titel, Doel and Einddatum gewijzigd.",
                "action_flag": list(LOG_ACTIONS[CHANGE]),
                "content_object_repr": f"Updated",
            },
        )

    @freeze_time("2021-10-18 13:00:00")
    def test_deleted_object_is_logged(self):
        plan = PlanFactory(created_by=self.user)
        url = reverse("admin:plans_plan_delete", kwargs={"object_id": plan.id})
        delete_form = self.app.get(url, user=self.user).forms[0]
        delete_form.submit()

        log_entry = TimelineLog.objects.last()
        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": "",
                "action_flag": list(LOG_ACTIONS[DELETION]),
                "content_object_repr": str(plan),
            },
        )

    def test_user_does_not_have_add_permission(self):
        url = reverse("admin:timeline_logger_timelinelog_add")
        response = self.app.get(url, user=self.user, expect_errors=True)
        self.assertEqual(response.status_code, 403)

    def test_superuser_does_not_have_add_permission(self):
        log_url = reverse("admin:timeline_logger_timelinelog_add")
        response = self.app.get(log_url, user=self.user, expect_errors=True)
        self.assertEqual(response.status_code, 403)

    def test_superuser_does_not_have_change_permission(self):
        add_url = reverse("admin:plans_plan_add")
        add_form = self.app.get(add_url, user=self.user).forms.get("plan_form")
        add_form["title"] = self.plan.title
        add_form["goal"] = self.plan.goal
        add_form["description"] = self.plan.description
        add_form["end_date"] = self.plan.end_date
        add_form["created_by"] = self.user.id
        add_form.submit()
        log_entry = TimelineLog.objects.first()
        log_url = reverse(
            "admin:timeline_logger_timelinelog_change",
            kwargs={"object_id": log_entry.id},
        )
        response = self.app.post(log_url, user=self.user, expect_errors=True)
        self.assertEqual(response.status_code, 403)

    def test_superuser_does_not_have_delete_permission(self):
        add_url = reverse("admin:plans_plan_add")
        add_form = self.app.get(add_url, user=self.user).forms.get("plan_form")
        add_form["title"] = self.plan.title
        add_form["goal"] = self.plan.goal
        add_form["description"] = self.plan.description
        add_form["end_date"] = self.plan.end_date
        add_form["created_by"] = self.user.id
        add_form.submit()
        log_entry = TimelineLog.objects.first()
        log_url = reverse(
            "admin:timeline_logger_timelinelog_delete",
            kwargs={"object_id": log_entry.id},
        )
        response = self.app.post(log_url, user=self.user, expect_errors=True)
        self.assertEqual(response.status_code, 403)

    def test_get_action_returns_addition_when_object_is_added(self):
        url = reverse("admin:plans_plan_add")
        form = self.app.get(url, user=self.user).forms.get("plan_form")
        form["title"] = self.plan.title
        form["goal"] = self.plan.goal
        form["description"] = self.plan.description
        form["end_date"] = self.plan.end_date
        form["created_by"] = self.user.id
        form.submit()

        log_entry = TimelineLog.objects.last()
        action = CustomTimelineLogAdmin.get_action_flag(
            CustomTimelineLogAdmin, log_entry
        )
        self.assertEqual(action, _("Aangemaakt"))

    def test_get_action_returns_change_when_object_is_modified(self):
        plan = PlanFactory()
        url = reverse("admin:plans_plan_change", kwargs={"object_id": plan.id})
        form = self.app.get(url, user=self.user).forms.get("plan_form")
        form["title"] = "Updated"
        form.submit()

        log_entry = TimelineLog.objects.last()
        action = CustomTimelineLogAdmin.get_action_flag(
            CustomTimelineLogAdmin, log_entry
        )
        self.assertEqual(action, _("Gewijzigd"))

    def test_get_action_returns_delete_when_object_is_deleted(self):
        plan = PlanFactory()
        url = reverse("admin:plans_plan_delete", kwargs={"object_id": plan.id})
        form = self.app.get(url, user=self.user).forms[0]
        form.submit()

        log_entry = TimelineLog.objects.last()
        action = CustomTimelineLogAdmin.get_action_flag(
            CustomTimelineLogAdmin, log_entry
        )
        self.assertEqual(action, _("Verwijderd"))

    def test_get_action_returns_empty_string_when_no_extra_data_exists(self):
        plan = PlanFactory()
        TimelineLog.objects.create(content_object=plan, user=self.user)

        log_entry = TimelineLog.objects.last()
        action = CustomTimelineLogAdmin.get_action_flag(
            CustomTimelineLogAdmin, log_entry
        )
        self.assertEqual(action, "")

    def test_object_link_returns_right_link(self):
        self.add_instance()
        url = reverse("admin:timeline_logger_timelinelog_changelist")
        response = self.app.get(url, user=self.user)
        plan = Plan.objects.first()
        obj_link = reverse("admin:plans_plan_change", kwargs={"object_id": plan.id})
        self.assertContains(response, obj_link)


class TestTimelineLogExport(WebTest):
    @freeze_time("2021-10-18 13:00:00")
    def test_proper_data_is_exported(self):
        user = UserFactory(is_superuser=True, is_staff=True)
        form = self.app.get(
            reverse("admin:timeline_logger_timelinelog_export"), user=user
        ).forms[0]

        # csv format chosen
        form["file_format"] = "0"
        response = form.submit()
        exported_data = response.content.decode("utf-8").splitlines()
        log_entry = TimelineLog.objects.first()

        self.assertEqual(
            exported_data,
            [
                "extra_data,id,content_type,object_id,timestamp,user,template",
                f'"{log_entry.extra_data}",{log_entry.id},{log_entry.content_type_id},{log_entry.user.id},2021-10-18 15:00:00,{user.id},timeline_logger/default.txt',
            ],
        )
