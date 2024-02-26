from django.core.management.base import BaseCommand

from open_inwoner.configurations.emails import inform_admins_about_failing_emails


class Command(BaseCommand):
    help = "Send failed emails digest"

    def handle(self, *args, **options):
        result = inform_admins_about_failing_emails()

        if result is None:
            self.stdout.write("No failed emails digest sent")
        elif result == 0:
            self.stdout.write(self.style.ERROR("Failed sending failed emails digest"))
        else:
            self.stdout.write(self.style.SUCCESS("Sent failed emails digest"))
