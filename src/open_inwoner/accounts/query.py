from typing import TYPE_CHECKING

from django.db.models import Case, F, Max, OuterRef, Q, Subquery, When
from django.db.models.query import QuerySet

if TYPE_CHECKING:
    from open_inwoner.accounts.models import User


class MessageQuerySet(QuerySet):
    def get_conversations_for_user(self, user: "User") -> "MessageQuerySet":
        """
        I apologize;

        Summary:

            Returns every conversation involving user, newest first.

        Details:

            A conversation is a Message, annotated with:
                - other_user_id
                - other_user_email
                - other_user_first_name
                - other_user_infix
                - other_user_last_name

            other_user_id matches the value of either sender or receiver field,
            (based on which one  does not match me.pk).

            Conversations should be the newest messages with other_user_id.

            Conversations should be unique/distinct by other_user_id.

        """
        filtered_messages = (
            self.filter(Q(receiver=user) | Q(sender=user))
            .annotate(
                other_user_uuid=Case(
                    When(receiver=user, then=F("sender__uuid")),
                    default=F("receiver__uuid"),
                )
            )
            .order_by()
        )
        grouped_messages = (
            filtered_messages.filter(other_user_uuid=OuterRef("other_user_uuid"))
            .values("other_user_uuid")
            .annotate(max_id=Max("id"))
            .values("max_id")
        )
        result = (
            self.annotate(
                other_user_uuid=Case(
                    When(receiver=user, then=F("sender__uuid")),
                    default=F("receiver__uuid"),
                )
            )
            .filter(id=Subquery(grouped_messages))
            .annotate(
                other_user_first_name=Case(
                    When(receiver=user, then=F("sender__first_name")),
                    default=F("receiver__first_name"),
                )
            )
            .annotate(
                other_user_infix=Case(
                    When(receiver=user, then=F("sender__infix")),
                    default=F("receiver__infix"),
                )
            )
            .annotate(
                other_user_last_name=Case(
                    When(receiver=user, then=F("sender__last_name")),
                    default=F("receiver__last_name"),
                )
            )
            .order_by("-pk")
        )

        return result

    def get_messages_between_users(self, user, other_user) -> "MessageQuerySet":
        """grouped by date"""
        return (
            self.filter(
                Q(sender=user, receiver=other_user)
                | Q(sender=other_user, receiver=user)
            )
            .select_related(
                "sender",
                "receiver",
            )
            .order_by("-created_on")
        )

    def mark_seen(self, user, other_user) -> int:
        """
        Mark messages as seen between two users.
        Returns the number of updated messages.
        """
        return self.filter(receiver=user, sender=other_user, seen=False).update(
            seen=True
        )


class InviteQuerySet(QuerySet):
    def get_pending_invitations_for_user(self, user: "User") -> "InviteQuerySet":
        return self.filter(inviter=user, accepted=False).order_by("-pk")


class UserQuerySet(QuerySet):
    def get_pending_approvals(self, user):
        return self.filter(contacts_for_approval=user)

    def having_usable_email(self):
        return self.exclude(
            Q(email="")
            | Q(email__endswith="@example.org")
            | Q(email__endswith="@localhost")
        )
