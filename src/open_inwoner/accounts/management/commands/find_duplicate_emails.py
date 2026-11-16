from collections import defaultdict

from django.core.management.base import BaseCommand

from open_inwoner.accounts.choices import DigitalAddressType
from open_inwoner.accounts.models import (
    EMAIL_SHAREABLE_LOGIN_TYPES,
    DigitalAddress,
    User,
)


class Command(BaseCommand):
    help = (
        "Lists email addresses that are used by more than one user in a way that "
        "is not allowed (ignoring capitalisation, and including additional email "
        "addresses). Users with a duplicated login email cannot log in until the "
        "duplicate is resolved. Nothing is modified."
    )

    def handle(self, *args, **options):
        user_ids_by_email: defaultdict[str, set[int]] = defaultdict(set)

        users = User.objects.exclude(email="").values_list("pk", "email")
        for user_id, email in users.iterator():
            user_ids_by_email[email.casefold()].add(user_id)

        addresses = DigitalAddress.objects.filter(
            type=DigitalAddressType.email
        ).values_list("user_id", "value")
        for user_id, email in addresses.iterator():
            user_ids_by_email[email.casefold()].add(user_id)

        shared = {
            email: user_ids
            for email, user_ids in user_ids_by_email.items()
            if len(user_ids) > 1
        }
        users_by_id = User.objects.in_bulk(
            {user_id for user_ids in shared.values() for user_id in user_ids}
        )

        num_duplicates = 0
        for email, user_ids in sorted(shared.items()):
            users = [users_by_id[user_id] for user_id in sorted(user_ids)]
            # Mirrors User.email_taken_by_other_user(): sharing is only allowed
            # if every user involved has a shareable login type.
            if all(user.login_type in EMAIL_SHAREABLE_LOGIN_TYPES for user in users):
                continue

            num_duplicates += 1
            descriptions = ", ".join(
                f"{user.pk} ({user.login_type}, "
                f"{'active' if user.is_active else 'inactive'})"
                for user in users
            )
            self.stdout.write(f"{email}: users {descriptions}")

        if num_duplicates:
            self.stdout.write(
                self.style.WARNING(f"Found {num_duplicates} duplicated email(s)")
            )
        else:
            self.stdout.write(self.style.SUCCESS("No duplicated emails found"))
