from django.db.models import Case, Exists, F, Max, OuterRef, Q, Subquery, Value, When
from django.db.models.query import QuerySet


class MessageQuerySet(QuerySet):
    def get_conversations_for_user(self, me: "User") -> "MessageQuerySet":
        """
        I apologize;

        Summary:

            Returns every conversation involving me, newest first.

        Details:

            A conversation is a Message, annotated with:
                - other_user_id
                - other_user_email
                - other_user_first_name
                - other_user_last_name

            other_user_id matches the value of either sender or receiver field,
            (based on which one  does not match me.pk).

            Conversations should be the newest messages with other_user_id.

            Conversations should be unique/distinct by other_user_id.

        """
        filtered_messages = (
            self.filter(Q(receiver=me) | Q(sender=me))
            .annotate(
                other_user_id=Case(
                    When(receiver=me, then=F("sender")), default=F("receiver")
                )
            )
            .order_by()
        )
        grouped_messages = (
            filtered_messages.filter(other_user_id=OuterRef("other_user_id"))
            .values("other_user_id")
            .annotate(max_id=Max("id"))
            .values("max_id")
        )
        result = (
            self.annotate(
                other_user_id=Case(
                    When(receiver=me, then=F("sender")), default=F("receiver")
                )
            )
            .filter(id=Subquery(grouped_messages))
            .annotate(
                other_user_email=Case(
                    When(receiver=me, then=F("sender__email")),
                    default=F("receiver__email"),
                )
            )
            .annotate(
                other_user_first_name=Case(
                    When(receiver=me, then=F("sender__first_name")),
                    default=F("receiver__first_name"),
                )
            )
            .annotate(
                other_user_last_name=Case(
                    When(receiver=me, then=F("sender__last_name")),
                    default=F("receiver__last_name"),
                )
            )
            .order_by("-pk")
        )

        return result

    def get_messages_between_users(self, me, other_user) -> "MessageQuerySet":
        """grouped by date"""
        return (
            self.filter(
                Q(sender=me, receiver=other_user) | Q(sender=other_user, receiver=me)
            )
            .select_related(
                "sender",
                "receiver",
            )
            .order_by("-created_on")
        )

    def mark_seen(self, me, other_user) -> int:
        """
        Mark messages as seen between two users.
        Returns the number of updated messages.
        """
        return self.filter(receiver=me, sender=other_user, seen=False).update(seen=True)


class ContactQuerySet(QuerySet):
    def get_extended_contacts_for_user(self, me):
        """
        Returns both active contacts and active reversed contacts for the user.
        The returned queryset is annotated with:
        - reverse (bool)
        - other_user_id
        - other_user_first_name
        - other_user_last_name
        - other_user_email
        - other_user_phonenumber (Null in case of reversed contacts)

        If the user and other user have contacts with each other only mine contact is shown
        """

        not_unique_emails = self.filter(
            created_by=me, email=OuterRef("created_by__email")
        ).values("email")
        return (
            self.filter(Q(contact_user=me) | Q(created_by=me))
            .annotate(reverse=Case(When(created_by=me, then=False), default=True))
            .annotate(
                other_user_id=Case(
                    When(created_by=me, then=F("contact_user")),
                    default=F("created_by"),
                )
            )
            .annotate(
                other_user_first_name=Case(
                    When(created_by=me, then=F("first_name")),
                    default=F("created_by__first_name"),
                )
            )
            .annotate(
                other_user_last_name=Case(
                    When(created_by=me, then=F("last_name")),
                    default=F("created_by__last_name"),
                )
            )
            .annotate(
                other_user_email=Case(
                    When(created_by=me, then=F("contact_user__email")),
                    default=F("created_by__email"),
                )
            )
            .annotate(
                other_user_phonenumber=Case(
                    When(created_by=me, then=F("phonenumber")),
                    default=Value(""),
                )
            )
        ).exclude(Exists(not_unique_emails), reverse=True)
