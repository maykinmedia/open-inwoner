import logging
from datetime import date
from typing import List

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.urls import reverse

from mail_editor.helpers import find_template

from open_inwoner.accounts.models import User
from open_inwoner.plans.models import Plan
from open_inwoner.utils.url import build_absolute_url

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send emails about expiring plans to the users"

    def handle(self, *args, **options):
        today = date.today()
        created_by_ids = list(
            Plan.objects.filter(end_date=today).values_list("created_by_id", flat=True)
        )
        contact_ids = list(
            Plan.objects.filter(end_date=today).values_list(
                "plan_contacts__id", flat=True
            )
        )

        user_ids = created_by_ids + contact_ids
        receivers = User.objects.filter(
            is_active=True, pk__in=user_ids, plans_notifications=True
        ).distinct()

        for receiver in receivers:
            """send email to each user"""
            plans = Plan.objects.filter(end_date=today).filter(
                Q(created_by=receiver) | Q(plan_contacts=receiver)
            )
            self.send_email(
                receiver=receiver,
                plans=plans,
            )

            logger.info(
                f"The email was sent to the user {receiver} about {plans.count()} expiring plans"
            )

    def send_email(self, receiver: User, plans: List[Plan]):
        plan_list_link = build_absolute_url(reverse("collaborate:plan_list"))
        template = find_template("expiring_plan")
        context = {
            "plans": plans,
            "plan_list_link": plan_list_link,
        }

        return template.send_email([receiver.email], context)
