from django.core.management import BaseCommand

from open_inwoner.accounts.models import User
from open_inwoner.userfeed.hooks.common import simple_message


class Command(BaseCommand):
    help = "Development tool to add items to UserFeed (for safety only enabled for active staff users)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user",
            help="User ID.",
            default=0,
        )
        parser.add_argument(
            "--message",
            help="Message text",
            default="",
        )
        parser.add_argument(
            "--title",
            help="Message title",
            default="",
        )
        parser.add_argument(
            "--url",
            help="Action URL",
            default="",
        )

    def handle(self, *args, **options):
        try:
            user = User.objects.get(pk=options["user"])
        except User.DoesNotExist:
            self.stdout.write("user_id not found, use one off:")
            for user in User.objects.filter(is_active=True, is_staff=True).order_by(
                "id"
            ):
                self.stdout.write(f"{user.id} - {user}")
            return

        print(user)

        if not options["message"] or not options["title"]:
            self.stdout.write("specify --title and/or --message")
            return

        simple_message(
            user, options["message"], title=options["title"], url=options["url"]
        )
