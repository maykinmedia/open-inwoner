import logging

from django.core.management import call_command

from open_inwoner.celery import app

logger = logging.getLogger(__name__)


@app.task
def send_failed_email_digest():
    logger.info("starting send_failed_email_digest() task")

    call_command("send_failed_email_digest")

    logger.info("finished send_failed_email_digest() task")
