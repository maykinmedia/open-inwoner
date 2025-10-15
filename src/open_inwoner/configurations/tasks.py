import io

from django.core.management import call_command

import structlog

from open_inwoner.celery import app

logger = structlog.stdlib.get_logger(__name__)


@app.task
def send_failed_mail_digest():
    logger.info("starting send_failed_mail_digest() task")

    out = io.StringIO()

    call_command("send_failed_mail_digest", stdout=out)

    logger.info("finished send_failed_mail_digest() task")

    return out.getvalue()
