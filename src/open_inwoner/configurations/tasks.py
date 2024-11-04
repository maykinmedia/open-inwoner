import io
import logging

from django.core.management import call_command

from open_inwoner.celery import app

logger = logging.getLogger(__name__)


@app.task
def send_failed_mail_digest():
    logger.info("starting send_failed_mail_digest() task")

    out = io.StringIO()

    call_command("send_failed_mail_digest", stdout=out)

    logger.info("finished send_failed_mail_digest() task")

    return out.getvalue()
